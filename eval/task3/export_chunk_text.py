"""Read-only export of full retrieved chunk text for Task 3 evidence review.

Reads the review CSV and the local Chroma DB, and writes one JSON object per
review row (question, strategy, rank, chunk_id, doc_id, pages, section, full
chunk text) to a JSONL file. It never writes to Chroma or the source PDFs and
refuses to overwrite an existing output file.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import chromadb


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default="./chroma_db")
    parser.add_argument("--collection-base", default="policylens_v1")
    parser.add_argument("--review-csv", default="eval/task3/evidence_review.csv")
    parser.add_argument("--output", default="eval/task3/chunk_text.jsonl")
    args = parser.parse_args()

    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"{output} already exists; choose a new --output path.")

    with Path(args.review_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("The evidence-review CSV contains no rows.")

    client = chromadb.PersistentClient(path=args.db_path)
    texts: dict[tuple[str, str], tuple[str, dict]] = {}
    for strategy in ("fixed", "structure"):
        ids = list(dict.fromkeys(r["chunk_id"] for r in rows if r["strategy"] == strategy))
        if not ids:
            continue
        collection = client.get_collection(f"{args.collection_base}_{strategy}")
        result = collection.get(ids=ids, include=["documents", "metadatas"])
        for cid, doc, meta in zip(result["ids"], result["documents"], result["metadatas"]):
            texts[(strategy, cid)] = (doc or "", meta or {})

    missing = 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for r in rows:
            text, meta = texts.get((r["strategy"], r["chunk_id"]), ("", {}))
            missing += not text
            handle.write(json.dumps({
                "question_id": r["question_id"],
                "strategy": r["strategy"],
                "rank": int(r["rank"]),
                "chunk_id": r["chunk_id"],
                "doc_id": r["doc_id"],
                "page_start": r["page_start"],
                "page_end": r["page_end"],
                "section_title": meta.get("section_title", ""),
                "chunk_text": text,
            }, ensure_ascii=False) + "\n")
    print(f"Rows written: {len(rows)}; chunks with no text: {missing}; output: {output}")


if __name__ == "__main__":
    main()
