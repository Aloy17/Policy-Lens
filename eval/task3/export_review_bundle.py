"""Export a read-only Task 3 review bundle from the local Chroma DB and source PDFs.

The output PDF contains every retrieved chunk in the evidence-review CSV, followed
by each unique cited source PDF page. It does not modify Chroma or source files.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import chromadb
import fitz


def add_text_page(doc: fitz.Document, heading: str, body: str) -> None:
    """Add one or more readable text pages, splitting long chunk text safely."""
    parts = [body[i:i + 4200] for i in range(0, max(len(body), 1), 4200)]
    for index, part in enumerate(parts, start=1):
        page = doc.new_page()
        suffix = f" (continued {index}/{len(parts)})" if len(parts) > 1 else ""
        page.insert_textbox(
            fitz.Rect(42, 36, 553, 76),
            heading + suffix,
            fontsize=9,
            fontname="helv",
        )
        page.insert_textbox(
            fitz.Rect(42, 88, 553, 800),
            part or "[No chunk text returned]",
            fontsize=7.5,
            fontname="cour",
            lineheight=1.15,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a PDF bundle for human review of Task 3 retrieval evidence."
    )
    parser.add_argument("--db-path", default="./chroma_db")
    parser.add_argument("--collection-base", default="policylens_v1")
    parser.add_argument("--review-csv", default="eval/task3/evidence_review.csv")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--output", default="eval/task3/review_bundle.pdf")
    args = parser.parse_args()

    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(
            f"{output_path} already exists; choose a new --output path to avoid overwriting it."
        )

    with Path(args.review_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("The evidence-review CSV contains no rows.")

    client = chromadb.PersistentClient(path=args.db_path)
    collections = {
        "fixed": client.get_collection(f"{args.collection_base}_fixed"),
        "structure": client.get_collection(f"{args.collection_base}_structure"),
    }

    retrieved: dict[tuple[str, str], tuple[str, dict]] = {}
    # A chunk may appear in multiple questions/ranks. Chroma requires unique IDs
    # per get() call, so fetch each strategy-specific chunk only once.
    ids_by_strategy = {
        strategy: list(dict.fromkeys(
            row["chunk_id"] for row in rows if row["strategy"] == strategy
        ))
        for strategy in ("fixed", "structure")
    }
    for strategy, ids in ids_by_strategy.items():
        if not ids:
            continue
        result = collections[strategy].get(
            ids=ids, include=["documents", "metadatas"]
        )
        for chunk_id, text, metadata in zip(
            result.get("ids") or [],
            result.get("documents") or [],
            result.get("metadatas") or [],
        ):
            retrieved[(strategy, chunk_id)] = (text or "", metadata or {})

    bundle = fitz.open()
    missing_chunks = []
    source_pages: set[tuple[str, int]] = set()

    for row in rows:
        strategy = row["strategy"]
        chunk_id = row["chunk_id"]
        chunk_text, metadata = retrieved.get((strategy, chunk_id), ("", {}))
        heading = (
            f'{row["question_id"]} | {strategy} rank {row["rank"]} | '
            f'{row["doc_id"]} pp. {row["page_start"]}-{row["page_end"]} | {chunk_id}'
        )
        if not chunk_text:
            missing_chunks.append(f"{strategy}:{chunk_id}")
        meta_text = (
            f"\n\nStored metadata: {metadata}\n"
            f"Source text:\n{chunk_text}"
        )
        add_text_page(bundle, heading, meta_text)

        try:
            start, end = int(row["page_start"]), int(row["page_end"])
        except (TypeError, ValueError):
            continue
        for page_number in range(start, end + 1):
            source_pages.add((row["doc_id"], page_number))

    pdf_root = Path(args.pdf_dir)
    source_page_count = 0
    missing_source_pages = []
    for doc_id, page_number in sorted(source_pages):
        source_path = pdf_root / f"{doc_id}.pdf"
        if not source_path.is_file():
            missing_source_pages.append(f"{doc_id} page {page_number}: PDF not found")
            continue
        try:
            with fitz.open(source_path) as source:
                page_index = page_number - 1
                if page_index < 0 or page_index >= source.page_count:
                    missing_source_pages.append(
                        f"{doc_id} page {page_number}: outside PDF page count {source.page_count}"
                    )
                    continue
                add_text_page(
                    bundle,
                    f"SOURCE PAGE | {doc_id} | PDF page {page_number}",
                    "Original source page follows.",
                )
                bundle.insert_pdf(source, from_page=page_index, to_page=page_index)
                source_page_count += 1
        except Exception as exc:
            missing_source_pages.append(f"{doc_id} page {page_number}: {exc}")

    if missing_chunks or missing_source_pages:
        report = [
            f"Missing Chroma chunks: {len(missing_chunks)}",
            *missing_chunks,
            "",
            f"Missing source pages: {len(missing_source_pages)}",
            *missing_source_pages,
        ]
        add_text_page(bundle, "EXPORT WARNINGS", "\n".join(report))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    bundle.set_metadata({
        "title": "PolicyLens Task 3 evidence review bundle",
        "author": "PolicyLens evaluation utility",
        "subject": "Retrieved chunks and original cited PDF pages",
    })
    bundle.save(output_path, garbage=4, deflate=True)
    bundle.close()

    print(f"Review rows: {len(rows)}")
    print(f"Retrieved chunks included: {len(retrieved)}")
    print(f"Unique original PDF pages included: {source_page_count}")
    print(f"Missing chunks: {len(missing_chunks)}")
    print(f"Missing source pages: {len(missing_source_pages)}")
    print(f"Created: {output_path}")


if __name__ == "__main__":
    main()
