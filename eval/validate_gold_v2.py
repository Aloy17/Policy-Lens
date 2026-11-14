"""Validate the v2 retrieval gold set (structure, manifest bounds, PDF evidence).

Structural checks run without PDFs. With --pdf-dir, every gold passage is also
checked against the original PDF: each term in passage_terms must appear in the
text of that passage's inclusive page range. Pages with no native text are
OCR'd only when --ocr is given; otherwise those passages are reported as
SKIPPED, never as passed.

    PYTHONPATH=. python eval/validate_gold_v2.py \
        --questions eval/benchmark_2026-11-14/gold_questions_v2.csv \
        --pdf-dir data/pdfs --ocr --report eval/benchmark_2026-11-14/dataset_validation_report.md
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieval_metrics import parse_passages  # noqa: E402

REQUIRED_COLUMNS = [
    "id", "question", "expected_doc_id", "expected_page_start", "expected_page_end",
    "is_table_question", "is_paraphrased", "gold_passages", "passage_terms",
    "requires_multiple_passages", "categories", "label_status", "include_in_headline",
    "source_origin", "validation_notes",
]
STATUSES = {"verified", "corrected", "invalid"}
CATEGORIES = {
    "direct", "paraphrase", "multi_passage", "table", "numeric_date", "clause", "distinction",
}


def normalise(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def load_manifest(path: Path) -> dict[str, int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {r["doc_id"].strip(): int(r["page_count"]) for r in csv.DictReader(handle)}


def validate_structure(rows: list[dict], page_counts: dict[str, int]) -> list[str]:
    errors: list[str] = []
    ids = [r["id"] for r in rows]
    for dup, n in Counter(ids).items():
        if n > 1:
            errors.append(f"{dup}: duplicate id.")
    questions = Counter(normalise(r["question"]) for r in rows)
    for text, n in questions.items():
        if n > 1:
            errors.append(f"duplicate question text: {text[:60]!r}")
    for r in rows:
        qid = r["id"]
        if not r["question"].strip():
            errors.append(f"{qid}: empty question.")
        if r["label_status"] not in STATUSES:
            errors.append(f"{qid}: label_status must be one of {sorted(STATUSES)}.")
        for flag in ("is_table_question", "is_paraphrased", "requires_multiple_passages", "include_in_headline"):
            if r[flag].lower() not in {"true", "false"}:
                errors.append(f"{qid}: {flag} must be true or false.")
        cats = set(filter(None, r["categories"].split("|")))
        if not cats or not cats <= CATEGORIES:
            errors.append(f"{qid}: unknown or empty categories {sorted(cats - CATEGORIES)}.")
        try:
            passages = parse_passages(r["gold_passages"])
        except ValueError as error:
            errors.append(f"{qid}: {error}")
            continue
        for p in passages:
            if p.doc_id not in page_counts:
                errors.append(f"{qid}: document {p.doc_id!r} absent from manifest.")
            elif p.page_end > page_counts[p.doc_id]:
                errors.append(f"{qid}: page {p.page_end} exceeds {p.doc_id} page_count {page_counts[p.doc_id]}.")
        if (len(passages) > 1) != (r["requires_multiple_passages"].lower() == "true"):
            errors.append(f"{qid}: requires_multiple_passages disagrees with gold_passages.")
        if (len(passages) > 1) != ("multi_passage" in cats):
            errors.append(f"{qid}: multi_passage category disagrees with gold_passages.")
        if (r["is_table_question"].lower() == "true") != ("table" in cats):
            errors.append(f"{qid}: is_table_question disagrees with categories.")
        if (r["is_paraphrased"].lower() == "true") != ("paraphrase" in cats):
            errors.append(f"{qid}: is_paraphrased disagrees with categories.")
        terms = r["passage_terms"].split(";")
        if len(terms) != len(passages):
            errors.append(f"{qid}: passage_terms must have one ';'-separated entry per gold passage.")
        if r["label_status"] == "invalid" and r["include_in_headline"].lower() == "true":
            errors.append(f"{qid}: invalid questions must be excluded from the headline.")
        if r["label_status"] != "invalid" and r["include_in_headline"].lower() != "true":
            errors.append(f"{qid}: only invalid questions may be excluded from the headline.")
    return errors


def page_texts(pdf_path: Path, ocr: bool) -> tuple[list[str], set[int]]:
    import pymupdf

    texts, ocr_pages = [], set()
    with pymupdf.open(pdf_path) as doc:
        for index, page in enumerate(doc, 1):
            text = page.get_text()
            if not text.strip() and ocr:
                with tempfile.TemporaryDirectory() as tmp:
                    image = Path(tmp) / "page.png"
                    page.get_pixmap(dpi=200).save(str(image))
                    result = subprocess.run(
                        ["tesseract", str(image), "-", "--psm", "4"],
                        capture_output=True, text=True, check=False,
                    )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"Tesseract failed on {pdf_path.name} page {index}: "
                        f"{result.stderr.strip() or 'unknown OCR error'}"
                    )
                text = result.stdout
                if text.strip():
                    ocr_pages.add(index)
            texts.append(text)
    return texts, ocr_pages


def validate_evidence(rows: list[dict], pdf_dir: Path, ocr: bool) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    details: list[dict] = []
    cache: dict[str, tuple[list[str], set[int]]] = {}
    for r in rows:
        if r["label_status"] == "invalid":
            details.append({"id": r["id"], "result": "EXCLUDED (invalid label)", "note": ""})
            continue
        passages = parse_passages(r["gold_passages"])
        for p, term_group in zip(passages, r["passage_terms"].split(";")):
            pdf = pdf_dir / f"{p.doc_id}.pdf"
            if not pdf.is_file():
                errors.append(f"{r['id']}: PDF not found: {pdf}")
                continue
            label = f"{p.doc_id}:{p.page_start}-{p.page_end}"
            try:
                if p.doc_id not in cache:
                    cache[p.doc_id] = page_texts(pdf, ocr)
                texts, ocr_pages = cache[p.doc_id]
                span = " ".join(texts[p.page_start - 1:p.page_end])
            except Exception as error:
                errors.append(f"{r['id']}: evidence extraction failed on {label}: {error}")
                details.append({"id": r["id"], "result": "FAIL (extraction error)", "note": label})
                continue
            if not span.strip():
                reason = "no native text and OCR disabled" if not ocr else "no text after OCR"
                details.append({"id": r["id"], "result": "SKIPPED", "note": f"{label}: {reason}"})
                continue
            haystack = normalise(span)
            missing = [t for t in term_group.split("|") if t and normalise(t) not in haystack]
            used_ocr = any(pg in ocr_pages for pg in range(p.page_start, p.page_end + 1))
            if missing:
                errors.append(f"{r['id']}: terms not found on {label}: {missing}")
                details.append({"id": r["id"], "result": "FAIL", "note": f"{label} missing {missing}"})
            else:
                details.append({"id": r["id"], "result": "PASS" + (" (OCR)" if used_ocr else ""), "note": label})
    return errors, details


def write_report(path: Path, rows, struct_errors, evidence_errors, details, ran_evidence, args) -> None:
    status = Counter(r["label_status"] for r in rows)
    cats = Counter(c for r in rows for c in r["categories"].split("|"))
    docs = sorted({p.doc_id for r in rows for p in parse_passages(r["gold_passages"])})
    lines = [
        "# Gold set v2: dataset validation report", "",
        f"Questions file: `{args.questions}`", f"Questions: {len(rows)}", "",
        "## Result", "",
        f"- Structural checks: {'PASSED' if not struct_errors else 'FAILED (' + str(len(struct_errors)) + ')'}",
        f"- PDF evidence checks: {('FAILED (' + str(len(evidence_errors)) + ' errors)' if evidence_errors else 'PASSED WITH SKIPS' if any(d['result'].startswith('SKIPPED') for d in details) else 'PASSED') if ran_evidence else 'not run'}",
        f"- Label status: {dict(status)}", f"- Category counts: {dict(sorted(cats.items()))}",
        f"- Documents covered ({len(docs)} of 37): {', '.join(docs)}", "",
    ]
    if struct_errors or evidence_errors:
        lines += ["## Errors", ""] + [f"- {e}" for e in struct_errors + evidence_errors] + [""]
    if details:
        lines += ["## Per-question PDF evidence check", "", "| id | result | passage / note |", "|---|---|---|"]
        lines += [f"| {d['id']} | {d['result']} | {d['note']} |" for d in details]
        lines += [""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", default="eval/benchmark_2026-11-14/gold_questions_v2.csv")
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--pdf-dir", default=None)
    parser.add_argument("--ocr", action="store_true", help="OCR pages that have no native text.")
    parser.add_argument("--allow-skipped-evidence", action="store_true",
                        help="Return success when some PDF evidence checks are SKIPPED (not recommended).")
    parser.add_argument("--report", default=None, help="Write a markdown report here.")
    args = parser.parse_args()

    with Path(args.questions).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_COLUMNS:
            print(f"Invalid columns. Expected: {REQUIRED_COLUMNS}")
            return 2
        rows = list(reader)

    struct_errors = validate_structure(rows, load_manifest(Path(args.manifest)))
    evidence_errors: list[str] = []
    details: list[dict] = []
    if args.pdf_dir:
        evidence_errors, details = validate_evidence(rows, Path(args.pdf_dir), args.ocr)

    if args.report:
        write_report(Path(args.report), rows, struct_errors, evidence_errors, details, bool(args.pdf_dir), args)

    skipped = [d for d in details if d["result"].startswith("SKIPPED")]
    errors = struct_errors + evidence_errors
    if skipped and args.pdf_dir and not args.allow_skipped_evidence:
        errors.append(
            f"{len(skipped)} PDF evidence passage check(s) were SKIPPED; "
            "rerun with working OCR or explicitly pass --allow-skipped-evidence."
        )
    if errors:
        print("Gold-set v2 validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Gold-set v2 validation PASSED.")
    if skipped:
        print("WARNING: evidence checks were skipped; this is not a complete PDF validation.")
    print(f"Questions: {len(rows)}; statuses: {dict(Counter(r['label_status'] for r in rows))}")
    if args.pdf_dir:
        print(f"PDF evidence: {sum(d['result'].startswith('PASS') for d in details)} passed, {len(skipped)} skipped")
    else:
        print("PDF evidence checks not run (no --pdf-dir).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
