"""Select a reproducible random sample of PDF pages for manual quality review."""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--output", default="eval/manual_inspection_template.csv")
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    pdf_dir = Path(args.pdf_dir)
    output_path = Path(args.output)
    if args.sample_size < 1:
        raise ValueError("--sample-size must be positive.")

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        documents = list(csv.DictReader(handle))
    if not documents:
        raise ValueError(f"No manifest rows found in {manifest_path}.")

    population = []
    missing = []
    for row in documents:
        doc_id = row["doc_id"]
        pdf_path = pdf_dir / f"{doc_id}.pdf"
        if not pdf_path.is_file():
            missing.append(doc_id)
            continue
        with pymupdf.open(pdf_path) as pdf:
            population.extend((doc_id, page_number) for page_number in range(1, len(pdf) + 1))

    if missing:
        raise FileNotFoundError(
            "PDFs missing for manifest documents: " + ", ".join(missing)
        )
    if args.sample_size > len(population):
        raise ValueError(
            f"Requested {args.sample_size} pages from population of {len(population)}."
        )

    rng = random.Random(args.seed)
    selected = sorted(rng.sample(population, args.sample_size))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "sample_id", "doc_id", "pdf_page", "printed_page", "layout_type",
        "source_text_present", "ocr_used", "ocr_reference_words",
        "ocr_correct_words", "estimated_word_accuracy", "table_present",
        "table_extraction_complete", "reading_order_correct",
        "header_footer_removed", "cleaning_removed_legitimate_text",
        "quality_issue", "notes",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, (doc_id, page_number) in enumerate(selected, start=1):
            writer.writerow({
                "sample_id": f"S{index:02d}",
                "doc_id": doc_id,
                "pdf_page": page_number,
            })

    print(f"PDF pages in sampling frame: {len(population)}")
    print(f"Sample size: {len(selected)}")
    print(f"Random seed: {args.seed}")
    print(f"Saved review template: {output_path}")
    for doc_id, page_number in selected:
        print(f"{doc_id}, page {page_number}")


if __name__ == "__main__":
    main()
