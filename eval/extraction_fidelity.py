"""Run deterministic extraction-fidelity checks against selected corpus PDF pages.

The checks are deliberately split into:
- automated assertions for known, stable source facts;
- review flags for complex layouts that need visual inspection.

This is not a corpus-wide accuracy estimate. It reads PDFs and parser output only;
it does not touch Chroma or change source files.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from src.parser import parse_pdf
from src.ocr import apply_ocr_to_pages


CASES: list[dict[str, Any]] = [
    {
        "case_id": "S03_depository_risk_table",
        "doc_id": "sebi_master_circular_for_depositories",
        "page": 170,
        "kind": "table",
        "required": ["High risk", "3", "Medium High risk", "2", "Medium risk", "1.5", "Low risk", "1"],
        "forbidden": ["15 .", "Mediumrisk"],
        "description": "Risk-category multiplier table; decimal fidelity is critical.",
    },
    {
        "case_id": "S05_lodr_wide_table",
        "doc_id": "sebi_master_circular_for_listing_obligations_and_disclosure_requirements_20",
        "page": 82,
        "kind": "wide_table",
        "required": ["Table IV", "Category", "PAN", "Voting Rights", "Custodian/DR Holder"],
        "forbidden": [],
        "description": "Wide multi-level shareholding table; inspect header-to-column relationships visually.",
    },
    {
        "case_id": "S06_brsr_cross_reference",
        "doc_id": "sebi_master_circular_for_listing_obligations_and_disclosure_requirements_20",
        "page": 213,
        "kind": "table",
        "required": ["Principle", "6", "Question", "7", "Essential Indicators"],
        "forbidden": [],
        "description": "BRSR Core table cross-reference; check cell text is not lost.",
    },
    {
        "case_id": "S07_merchant_bankers_rescinded",
        "doc_id": "sebi_master_circular_for_merchant_bankers",
        "page": 104,
        "kind": "table",
        "required": ["LIST OF RESCINDED CIRCULARS", "Circular No", "Subject", "SEBI RMB CIRCULAR"],
        "forbidden": [],
        "description": "Multi-column circular/date/subject association; requires visual row-association review.",
    },
    {
        "case_id": "S08_mutual_fund_invit_limits",
        "doc_id": "sebi_master_circular_for_mutual_funds",
        "page": 217,
        "kind": "table",
        "required": ["10% of units", "10% of NAV", "5% of NAV", "single issuer", "InvIT"],
        "forbidden": [],
        "description": "Investment-limit table; preserve three distinct limit/qualifier relationships.",
    },
    {
        "case_id": "OCR_gazette_1981_p2",
        "doc_id": "gazette_1981_special_bearer_bonds",
        "page": 2,
        "kind": "ocr_reference",
        "required": ["Special Bearer Bonds", "1981", "article 123", "whole of India"],
        "forbidden": [],
        "description": "Scanned Gazette page with a committed human-transcribed OCR reference.",
    },
    {
        "case_id": "OCR_pfrda_p27",
        "doc_id": "pfrda_master_circular_kyc_aml_cft",
        "page": 27,
        "kind": "ocr_reference",
        "required": ["Video based Customer Identification Process", "PFRDA", "October 06, 2020"],
        "forbidden": [],
        "description": "PFRDA scanned/mixed page with a committed human-transcribed OCR reference.",
    },
]


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def inspect_case(pdf_dir: Path, case: dict[str, Any]) -> dict[str, Any]:
    pdf_path = pdf_dir / f"{case['doc_id']}.pdf"
    if not pdf_path.is_file():
        return {
            "case_id": case["case_id"],
            "doc_id": case["doc_id"],
            "page": case["page"],
            "status": "missing_pdf",
            "missing_required": case["required"],
            "forbidden_found": [],
            "table_count": None,
            "word_count": None,
            "description": case["description"],
        }

    pages = parse_pdf(pdf_path)
    page = next((item for item in pages if item["page_number"] == case["page"]), None)
    if page is None:
        return {
            "case_id": case["case_id"],
            "doc_id": case["doc_id"],
            "page": case["page"],
            "status": "page_out_of_range",
            "missing_required": case["required"],
            "forbidden_found": [],
            "table_count": None,
            "word_count": None,
            "description": case["description"],
        }

    inspected_page = page
    if case["kind"] == "ocr_reference":
        # Exercise the production OCR fallback on this page, not merely the
        # PDF's embedded text layer. Tesseract must be installed locally.
        inspected_page = apply_ocr_to_pages(pdf_path, [page], enabled=True)[0]

    text = _normalise(inspected_page["text"])
    missing = [term for term in case["required"] if _normalise(term) not in text]
    forbidden = [term for term in case["forbidden"] if _normalise(term) in text]
    status = "pass" if not missing and not forbidden else "fail"
    return {
        "case_id": case["case_id"],
        "doc_id": case["doc_id"],
        "page": case["page"],
        "kind": case["kind"],
        "status": status,
        "missing_required": missing,
        "forbidden_found": forbidden,
        "table_count": page.get("table_count", 0),
        "word_count": len(inspected_page["text"].split()),
        "ocr_used": bool(inspected_page.get("ocr_used", False)),
        "ocr_candidate": page.get("word_count", 0) < 20
        or (
            page.get("image_coverage", 0.0) >= 0.5
            and page.get("word_count", 0) < 120
        ),
        "description": case["description"],
    }


def run(pdf_dir: Path) -> dict[str, Any]:
    results = [inspect_case(pdf_dir, case) for case in CASES]
    passed = sum(item["status"] == "pass" for item in results)
    failed = sum(item["status"] == "fail" for item in results)
    unavailable = len(results) - passed - failed
    return {
        "schema_version": 1,
        "scope": "seven deterministic pages; extraction smoke checks, not corpus-wide accuracy",
        "summary": {
            "cases": len(results),
            "passed": passed,
            "failed": failed,
            "unavailable": unavailable,
        },
        "results": results,
        "manual_review_required": [
            "S05 wide-table header and column relationships",
            "S07 circular number/date/subject row associations",
            "all flagged values against the rendered original PDF page",
            "OCR output against the committed human reference using eval/ocr_accuracy.py",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--output", default="eval/extraction_fidelity_report.json")
    args = parser.parse_args()

    report = run(Path(args.pdf_dir))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved: {output}")
    if report["summary"]["failed"] or report["summary"]["unavailable"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
