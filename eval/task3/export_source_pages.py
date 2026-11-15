"""Export only the original PDF pages referenced by Task 3 evidence rows.

Read-only: this script does not access or modify Chroma, source PDFs, or CSV inputs.
It writes page text as JSONL and a separate PDF for pages needing visual inspection.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import fitz


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"doc_id", "page_start", "page_end", "question_id", "strategy", "rank"}
    missing = required.difference(rows[0].keys() if rows else set())
    if missing:
        raise ValueError(f"Review CSV is missing columns: {sorted(missing)}")
    if not rows:
        raise ValueError("Review CSV contains no evidence rows.")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export source-page text and a targeted visual-review PDF for Task 3."
    )
    parser.add_argument("--review-csv", default="eval/task3/evidence_review.csv")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--text-output", default="eval/task3/source_pages.jsonl")
    parser.add_argument("--visual-output", default="eval/task3/source_pages_visual.pdf")
    parser.add_argument("--manifest-output", default="eval/task3/source_pages_manifest.csv")
    parser.add_argument(
        "--visual-word-threshold", type=int, default=80,
        help="Include pages with fewer extracted words in the visual-review PDF.",
    )
    args = parser.parse_args()

    review_path = Path(args.review_csv)
    pdf_root = Path(args.pdf_dir)
    text_path = Path(args.text_output)
    visual_path = Path(args.visual_output)
    manifest_path = Path(args.manifest_output)
    outputs = [text_path, visual_path, manifest_path]
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing output(s): " + ", ".join(existing)
            + ". Choose new output paths or move the old exports first."
        )

    rows = read_rows(review_path)
    document_pages: dict[str, set[int]] = defaultdict(set)
    page_context: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        doc_id = row["doc_id"].strip()
        try:
            start, end = int(row["page_start"]), int(row["page_end"])
        except (TypeError, ValueError):
            continue
        if not doc_id or start < 1 or end < start:
            continue
        for page_number in range(start, end + 1):
            document_pages[doc_id].add(page_number)
            page_context[(doc_id, page_number)].append({
                "question_id": row["question_id"],
                "strategy": row["strategy"],
                "rank": row["rank"],
                "chunk_id": row.get("chunk_id", ""),
            })

    document_types: dict[str, str] = {}
    with Path(args.manifest).open(encoding="utf-8-sig", newline="") as handle:
        for item in csv.DictReader(handle):
            document_types[item["doc_id"]] = item.get("document_type", "")

    missing_pages: list[str] = []
    visual_reasons: dict[tuple[str, int], str] = {}
    text_count = 0
    visual_count = 0
    text_path.parent.mkdir(parents=True, exist_ok=True)
    visual_bundle = fitz.open()

    with text_path.open("w", encoding="utf-8") as text_handle:
        for doc_id in sorted(document_pages):
            source_path = pdf_root / f"{doc_id}.pdf"
            if not source_path.is_file():
                missing_pages.append(f"{doc_id}: PDF not found at {source_path}")
                continue
            try:
                source = fitz.open(source_path)
            except Exception as exc:
                missing_pages.append(f"{doc_id}: cannot open PDF: {exc}")
                continue

            with source:
                for page_number in sorted(document_pages[doc_id]):
                    page_index = page_number - 1
                    if page_index < 0 or page_index >= source.page_count:
                        missing_pages.append(
                            f"{doc_id} page {page_number}: outside PDF page count {source.page_count}"
                        )
                        continue
                    page = source.load_page(page_index)
                    page_text = page.get_text("text", sort=True)
                    word_count = len(page_text.split())
                    doc_type = document_types.get(doc_id, "")
                    reasons = []
                    if doc_type == "scanned_or_mixed":
                        reasons.append("manifest_scanned_or_mixed")
                    if word_count < args.visual_word_threshold:
                        reasons.append(f"low_extracted_text_{word_count}_words")
                    visual_review = bool(reasons)
                    if visual_review:
                        visual_reasons[(doc_id, page_number)] = ";".join(reasons)

                    record = {
                        "doc_id": doc_id,
                        "pdf_file": source_path.name,
                        "pdf_page": page_number,
                        "document_type": doc_type,
                        "word_count": word_count,
                        "needs_visual_review": visual_review,
                        "visual_review_reason": ";".join(reasons),
                        "referenced_by": page_context[(doc_id, page_number)],
                        "page_text": page_text,
                    }
                    text_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    text_count += 1

                    if visual_review:
                        label = visual_bundle.new_page(width=595, height=842)
                        label.insert_textbox(
                            fitz.Rect(42, 35, 553, 95),
                            f"SOURCE PAGE | {doc_id} | PDF page {page_number}\n"
                            f"Reason: {', '.join(reasons)}",
                            fontsize=10,
                        )
                        visual_bundle.insert_pdf(
                            source, from_page=page_index, to_page=page_index
                        )
                        visual_count += 1

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "doc_id", "pdf_page", "word_count", "needs_visual_review",
            "visual_review_reason", "referenced_by",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for (doc_id, page_number), reason in sorted(visual_reasons.items()):
            writer.writerow({
                "doc_id": doc_id,
                "pdf_page": page_number,
                "word_count": "",
                "needs_visual_review": "yes",
                "visual_review_reason": reason,
                "referenced_by": ";".join(
                    f"{item['question_id']}:{item['strategy']}:r{item['rank']}"
                    for item in page_context[(doc_id, page_number)]
                ),
            })

    visual_bundle.set_metadata({
        "title": "PolicyLens Task 3 targeted source-page visual review",
        "author": "PolicyLens evaluation utility",
        "subject": "Only cited pages flagged as scanned/mixed or low-text",
    })
    visual_bundle.save(visual_path, garbage=4, deflate=True)
    visual_bundle.close()

    print(f"Evidence rows read: {len(rows)}")
    print(f"Unique source pages requested: {sum(map(len, document_pages.values()))}")
    print(f"Source pages exported as text: {text_count}")
    print(f"Pages included for visual review: {visual_count}")
    print(f"Missing/unreadable source entries: {len(missing_pages)}")
    if missing_pages:
        print("Missing entries:")
        for item in missing_pages:
            print(f"  - {item}")
    print(f"Text export: {text_path}")
    print(f"Visual-review PDF: {visual_path}")
    print(f"Visual-review manifest: {manifest_path}")


if __name__ == "__main__":
    main()
