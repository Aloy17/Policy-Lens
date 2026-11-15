"""Audit whether retrieved chunk text aligns with its cited source-page text.

This is a deterministic text-alignment check, not a semantic evidence review and
not a substitute for inspecting original PDF pages (especially scanned/table pages).
Inputs are read-only. Outputs are new files and are never overwritten.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

CHUNK_FIELDS = {"question_id", "strategy", "rank", "chunk_id", "doc_id",
                "page_start", "page_end", "chunk_text"}
SOURCE_FIELDS = {"doc_id", "pdf_page", "page_text"}


def read_jsonl(path: Path, required: set[str]) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            missing = required - row.keys()
            if missing:
                raise ValueError(f"{path}:{line_no}: missing fields {sorted(missing)}")
            rows.append(row)
    return rows


def tokens(value: str) -> list[str]:
    value = unicodedata.normalize("NFKD", value).lower()
    return re.findall(r"[a-z0-9]+", value)


def trigrams(values: list[str]) -> set[tuple[str, str, str]]:
    return set(zip(values, values[1:], values[2:]))


def audit(chunks: list[dict], source_rows: list[dict]) -> list[dict]:
    pages = {(r["doc_id"], int(r["pdf_page"])): r for r in source_rows}
    results = []
    for chunk in chunks:
        start, end = int(chunk["page_start"]), int(chunk["page_end"])
        cited = [pages[(chunk["doc_id"], p)] for p in range(start, end + 1)
                 if (chunk["doc_id"], p) in pages]
        missing = [p for p in range(start, end + 1)
                   if (chunk["doc_id"], p) not in pages]
        chunk_tokens = tokens(chunk["chunk_text"])
        page_tokens = tokens(" ".join(r["page_text"] for r in cited))
        chunk_grams, page_grams = trigrams(chunk_tokens), trigrams(page_tokens)
        coverage = (len(chunk_grams & page_grams) / len(chunk_grams)
                    if chunk_grams else 0.0)
        results.append({
            "question_id": chunk["question_id"],
            "strategy": chunk["strategy"],
            "rank": chunk["rank"],
            "chunk_id": chunk["chunk_id"],
            "doc_id": chunk["doc_id"],
            "page_start": start,
            "page_end": end,
            "chunk_words": len(chunk_tokens),
            "matched_trigrams": len(chunk_grams & page_grams),
            "chunk_trigrams": len(chunk_grams),
            "text_alignment": round(coverage, 4),
            "source_pages_found": len(cited),
            "source_pages_expected": end - start + 1,
            "missing_source_pages": ";".join(map(str, missing)),
            "needs_visual_review": any(r.get("needs_visual_review") for r in cited),
            "document_types": ";".join(sorted({r.get("document_type", "") for r in cited})),
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=Path("eval/task3/chunk_text.jsonl"))
    parser.add_argument("--source-pages", type=Path, default=Path("eval/task3/source_pages.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("eval/task3/source_alignment_audit.csv"))
    parser.add_argument("--summary", type=Path, default=Path("eval/task3/source_alignment_summary.json"))
    args = parser.parse_args()
    for path in (args.output, args.summary):
        if path.exists():
            raise FileExistsError(f"{path} already exists; choose a new output path.")
    chunks = read_jsonl(args.chunks, CHUNK_FIELDS)
    source_rows = read_jsonl(args.source_pages, SOURCE_FIELDS)
    rows = audit(chunks, source_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    alignments = [r["text_alignment"] for r in rows]
    summary = {
        "chunk_records": len(chunks),
        "source_page_records": len(source_rows),
        "chunks_with_all_source_pages": sum(
            r["source_pages_found"] == r["source_pages_expected"] for r in rows),
        "chunks_needing_visual_review": sum(r["needs_visual_review"] for r in rows),
        "alignment_bands": {
            band: sum(lo <= value < hi for value in alignments)
            for band, lo, hi in [
                ("0.95-1.00", .95, 1.01), ("0.80-0.95", .80, .95),
                ("0.50-0.80", .50, .80), ("0.01-0.50", .01, .50),
                ("0.00", 0, .000001),
            ]
        },
        "limitations": [
            "Text alignment does not establish semantic support for a question.",
            "Text alignment does not verify visual table structure or scanned-page content.",
            "This report does not set evidence_class, supported_fact_ids, citation_status, or source_verified.",
        ],
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
