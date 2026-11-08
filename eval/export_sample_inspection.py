"""Export sampled PDF pages with extracted, OCR and cleaned text for manual review."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

from src.parser import parse_pdf
from src.ocr import apply_ocr_to_pages
from src.cleaner import clean_pages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--sample", default="eval/manual_inspection_template.csv")
    parser.add_argument("--output", default="eval/manual_inspection_export.csv")
    parser.add_argument("--min-words", type=int, default=20)
    parser.add_argument("--image-coverage-threshold", type=float, default=0.5)
    parser.add_argument("--image-text-word-limit", type=int, default=120)
    parser.add_argument("--language", default="eng")
    args = parser.parse_args()

    sample = pd.read_csv(args.sample).fillna("")
    manifest = pd.read_csv(args.manifest).fillna("")
    documents = manifest.set_index("doc_id").to_dict("index")
    pdf_dir = Path(args.pdf_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "sample_id", "doc_id", "pdf_page", "page_count",
        "extracted_word_count", "image_coverage", "table_count",
        "ocr_triggered", "ocr_word_count", "cleaned_word_count",
        "removed_word_count", "original_text", "ocr_text", "cleaned_text",
    ]
    rows = []
    for doc_id, group in sample.groupby("doc_id", sort=True):
        if doc_id not in documents:
            raise KeyError(f"{doc_id} is not present in {args.manifest}")
        pdf_path = pdf_dir / f"{doc_id}.pdf"
        if not pdf_path.is_file():
            raise FileNotFoundError(pdf_path)

        pages = parse_pdf(pdf_path)
        selected_numbers = {int(value) for value in group["pdf_page"]}
        selected = [page for page in pages if page["page_number"] in selected_numbers]
        if len(selected) != len(selected_numbers):
            raise ValueError(f"One or more sampled pages are outside {doc_id}'s page range")

        # Apply OCR only to the sampled pages; preserve the pipeline's exact
        # thresholds and OCR implementation without spending time OCRing every page.
        ocr_pages = apply_ocr_to_pages(
            pdf_path,
            selected,
            min_words=args.min_words,
            language=args.language,
            enabled=True,
            image_coverage_threshold=args.image_coverage_threshold,
            image_text_word_limit=args.image_text_word_limit,
        )
        ocr_by_page = {p["page_number"]: p for p in ocr_pages}

        # Run the real cleaner across all extracted pages so repeated
        # header/footer detection uses the same document-wide context as ingestion.
        cleaned_all = clean_pages(pages)
        cleaned_by_page = {p["page_number"]: p for p in cleaned_all}

        for sample_row in group.to_dict("records"):
            page_number = int(sample_row["pdf_page"])
            source = next(p for p in pages if p["page_number"] == page_number)
            ocr = ocr_by_page[page_number]
            cleaned = cleaned_by_page[page_number]
            # If OCR was used by ingestion, its text is the pre-cleaning input.
            # Re-clean that sampled OCR result with the same cleaner.
            cleaned_ocr = clean_pages([ocr])[0] if ocr.get("ocr_used") else cleaned
            rows.append({
                "sample_id": sample_row["sample_id"],
                "doc_id": doc_id,
                "pdf_page": page_number,
                "page_count": len(pages),
                "extracted_word_count": source["word_count"],
                "image_coverage": round(source.get("image_coverage", 0.0), 4),
                "table_count": source.get("table_count", 0),
                "ocr_triggered": bool(ocr.get("ocr_used", False)),
                "ocr_word_count": len(ocr.get("text", "").split()) if ocr.get("ocr_used") else "",
                "cleaned_word_count": cleaned_ocr["word_count"],
                "removed_word_count": cleaned_ocr.get("removed_word_count", ""),
                "original_text": ocr.get("text", ""),
                "ocr_text": ocr.get("text", "") if ocr.get("ocr_used") else "",
                "cleaned_text": cleaned_ocr["text"],
            })

    rows.sort(key=lambda row: row["sample_id"])
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Sampled pages exported: {len(rows)}")
    print(f"Pages OCR-triggered: {sum(bool(row['ocr_triggered']) for row in rows)}")
    print(f"Pages with detected tables: {sum(int(row['table_count']) > 0 for row in rows)}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
