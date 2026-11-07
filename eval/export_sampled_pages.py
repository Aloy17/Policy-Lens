"""Export the deterministic Phase 3 page sample for manual quality inspection."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import pymupdf

from src.cleaner import clean_pages
from src.ocr import ocr_page
from src.parser import _extract_page_text, _extract_tables, _image_coverage


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", default="eval/manual_inspection_template.csv")
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--pdf-dir", required=True, help="Directory containing <doc_id>.pdf files.")
    parser.add_argument("--output-dir", default="eval/manual_inspection")
    parser.add_argument("--ocr-language", default="eng")
    parser.add_argument("--min-words", type=int, default=20)
    parser.add_argument("--image-coverage-threshold", type=float, default=0.5)
    parser.add_argument("--image-text-word-limit", type=int, default=120)
    parser.add_argument("--no-ocr", action="store_true")
    return parser.parse_args()


def needs_ocr(words, image_coverage, args):
    return words < args.min_words or (
        image_coverage >= args.image_coverage_threshold
        and words < args.image_text_word_limit
    )


def printed_page_hint(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in (lines[-1:] + lines[:1]):
        match = re.fullmatch(r"(?:page\s*)?(\d{1,4})", line, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def main():
    args = parse_args()
    template = pd.read_csv(args.template).fillna("")
    required = {"sample_id", "doc_id", "pdf_page"}
    if not required.issubset(template.columns):
        raise SystemExit("Sample template must contain sample_id, doc_id, and pdf_page.")
    if template.empty:
        raise SystemExit("Sample template is empty; run sample_inspection_pages.py first.")

    manifest = pd.read_csv(args.manifest, dtype=str).fillna("")
    if "doc_id" not in manifest.columns:
        raise SystemExit("Manifest must contain a doc_id column.")
    manifest_by_id = manifest.set_index("doc_id").to_dict("index")

    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = [
        "# PolicyLens sampled-page inspection",
        "",
        f"- Sample size: {len(template)}",
        f"- PDF directory: {pdf_dir}",
        f"- OCR execution: {'disabled' if args.no_ocr else 'enabled for pages meeting the configured triage rules'}",
        "",
        "PDF page numbers are 1-based. Printed-page hints are tentative and must be checked visually.",
        "OCR candidacy is a heuristic, not proof of a scan or OCR accuracy.",
        "Cleaning preview is applied to the sampled pages only; repeated-header detection therefore uses this sample, not the full source document. Treat it as an inspection aid, not a byte-for-byte reproduction of full-document ingestion cleaning.",
        "",
    ]
    metadata_rows = []
    review_pdf = pymupdf.open()

    for doc_id, group in template.groupby("doc_id", sort=False):
        source_pdf = pdf_dir / f"{doc_id}.pdf"
        if not source_pdf.is_file():
            raise SystemExit(f"PDF not found: {source_pdf}")

        with pymupdf.open(source_pdf) as document:
            sampled_numbers = {int(value) for value in group["pdf_page"]}
            page_data_by_number = {}

            for page_no in sorted(sampled_numbers):
                if page_no < 1 or page_no > len(document):
                    raise SystemExit(f"{doc_id}: page {page_no} is outside 1..{len(document)}.")
                page = document[page_no - 1]
                native_text = _extract_page_text(page)
                tables = _extract_tables(page)
                if tables:
                    native_text += "\n\n" + "\n\n".join(tables)
                coverage = _image_coverage(page)
                native_words = len(native_text.split())
                candidate = needs_ocr(native_words, coverage, args)
                ocr_text = ""
                ocr_used = False
                inspected_text = native_text

                if candidate and not args.no_ocr:
                    ocr_text = ocr_page(source_pdf, page_no, args.ocr_language)
                    ocr_used = True
                    if ocr_text.strip():
                        inspected_text = ocr_text.rstrip()
                        if tables:
                            inspected_text += "\n\n" + "\n\n".join(tables)

                page_data_by_number[page_no] = {
                    "native_text": native_text,
                    "tables": tables,
                    "coverage": coverage,
                    "native_words": native_words,
                    "candidate": candidate,
                    "ocr_text": ocr_text,
                    "ocr_used": ocr_used,
                    "inspected_text": inspected_text,
                }

            cleaned_input = [
                {
                    "page_number": page_no,
                    "text": data["inspected_text"],
                    "word_count": len(data["inspected_text"].split()),
                    "has_text": bool(data["inspected_text"].strip()),
                    "table_count": len(data["tables"]),
                    "table_text": "\n\n".join(data["tables"]),
                    "image_coverage": data["coverage"],
                }
                for page_no, data in page_data_by_number.items()
            ]
            cleaned_by_number = {
                page["page_number"]: page
                for page in clean_pages(cleaned_input)
            }

            report.extend(["---", "", f"## {doc_id}", ""])
            doc_meta = manifest_by_id.get(str(doc_id), {})
            if doc_meta:
                report.append(
                    f"Document: {doc_meta.get('title', '')} | Issuer: {doc_meta.get('issuer', '')}"
                )
                report.append("")

            for _, sample_row in group.iterrows():
                page_no = int(sample_row["pdf_page"])
                page = document[page_no - 1]
                data = page_data_by_number[page_no]
                cleaned = cleaned_by_number[page_no]
                blocks = [
                    block for block in page.get_text("blocks")
                    if len(block) > 4 and str(block[4]).strip()
                ]
                image_count = len(page.get_images(full=True))
                layout = (
                    "likely_scan_or_sparse_text" if data["candidate"]
                    else "image_heavy_mixed"
                    if data["coverage"] >= args.image_coverage_threshold
                    else "text_native"
                )

                metadata_rows.append({
                    "sample_id": sample_row["sample_id"],
                    "doc_id": doc_id,
                    "pdf_page": page_no,
                    "printed_page_hint": printed_page_hint(data["native_text"]),
                    "page_width_pt": round(page.rect.width, 2),
                    "page_height_pt": round(page.rect.height, 2),
                    "native_word_count": data["native_words"],
                    "native_char_count": len(data["native_text"]),
                    "cleaned_word_count": cleaned["word_count"],
                    "text_block_count": len(blocks),
                    "image_count": image_count,
                    "image_coverage": round(data["coverage"], 4),
                    "table_count": len(data["tables"]),
                    "ocr_candidate": data["candidate"],
                    "ocr_used": data["ocr_used"],
                    "ocr_word_count": len(data["ocr_text"].split()),
                    "layout_triage": layout,
                })

                report.extend([
                    f"### {sample_row['sample_id']} — PDF page {page_no}",
                    "",
                    f"- Layout triage: {layout}",
                    f"- Native extraction: {data['native_words']} words, {len(data['native_text'])} characters",
                    f"- Dimensions: {page.rect.width:.1f} × {page.rect.height:.1f} pt",
                    f"- Text blocks: {len(blocks)}; images: {image_count}; image coverage: {data['coverage']:.1%}",
                    f"- Detected tables: {len(data['tables'])}",
                    f"- OCR candidate: {data['candidate']}; OCR run: {data['ocr_used']}",
                    "",
                    "#### Native extracted text",
                    "",
                    data["native_text"].strip() or "[NO NATIVE TEXT EXTRACTED]",
                    "",
                ])
                if data["ocr_text"].strip():
                    report.extend(["#### OCR text", "", data["ocr_text"].strip(), ""])
                report.extend([
                    "#### Cleaned text",
                    "",
                    cleaned["text"].strip() or "[NO TEXT AFTER EXTRACTION/OCR]",
                    "",
                ])

                review_pdf.insert_pdf(document, from_page=page_no - 1, to_page=page_no - 1)
                review_pdf[-1].insert_text(
                    (24, 24),
                    f"{sample_row['sample_id']} | {doc_id} | PDF page {page_no}",
                    fontsize=8,
                    color=(0.8, 0.1, 0.1),
                    overlay=True,
                )

    report_path = output_dir / "inspection_report.md"
    metadata_path = output_dir / "inspection_metadata.csv"
    review_path = output_dir / "sampled_pages_review.pdf"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    pd.DataFrame(metadata_rows).to_csv(metadata_path, index=False)
    review_pdf.save(review_path, garbage=4, deflate=True)
    review_pdf.close()

    print(f"Sampled pages exported: {len(metadata_rows)}")
    print(f"Report: {report_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Visual review PDF: {review_path}")
    print("Source PDFs and the sample template were not modified.")


if __name__ == "__main__":
    main()
