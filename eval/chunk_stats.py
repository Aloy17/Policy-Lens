"""Report chunk token-size statistics for both chunking strategies.

Checks the brief's "chunks of 300 to 800 tokens" requirement and estimates how often a
table is split across chunks.

Two sources:
  --source db   read the stored chunks from a Chroma database (exact, uses the model tokenizer)
  --source pdf  re-chunk the PDFs with the same parse/clean/chunk code (no embedding, no OCR)

Token counting uses the embedding model's tokenizer. If the model cannot be loaded (for
example no network), pass --tokenizer whitespace; counts are then words, not model tokens,
so treat them as an approximation.

Usage:
    PYTHONPATH=. python eval/chunk_stats.py --source db \
        --db-path "dist/PolicyLens/PolicyLens Data/chroma_db" --collection policylens_v1
    PYTHONPATH=. python eval/chunk_stats.py --source pdf --tokenizer whitespace
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path
from typing import Callable, Iterable

MIN_TOKENS = 300
MAX_TOKENS = 800


def is_table_fragment(text: str) -> bool:
    """A chunk that starts inside a table: first line is a table row, no [TABLE n] header."""
    first = text.lstrip().splitlines()[0] if text.strip() else ""
    return first.startswith("|") and "[TABLE" not in text


def summarize(texts: Iterable[str], count_tokens: Callable[[str], int]) -> dict[str, float]:
    counts = []
    fragments = 0
    with_table = 0
    for text in texts:
        counts.append(count_tokens(text))
        if "[TABLE" in text:
            with_table += 1
        if is_table_fragment(text):
            fragments += 1
    if not counts:
        return {"chunks": 0}
    ordered = sorted(counts)

    def pct(p: float) -> int:
        return ordered[min(len(ordered) - 1, int(p * len(ordered)))]

    below = sum(1 for c in counts if c < MIN_TOKENS)
    above = sum(1 for c in counts if c > MAX_TOKENS)
    return {
        "chunks": len(counts),
        "min": ordered[0],
        "p5": pct(0.05),
        "median": int(statistics.median(ordered)),
        "p95": pct(0.95),
        "max": ordered[-1],
        f"below_{MIN_TOKENS}": below,
        f"below_{MIN_TOKENS}_pct": round(100 * below / len(counts), 1),
        f"above_{MAX_TOKENS}": above,
        "chunks_with_table_marker": with_table,
        "table_continuation_fragments": fragments,
    }


def make_counter(kind: str, model_name: str) -> tuple[Callable[[str], int], object | None]:
    if kind == "whitespace":
        return (lambda text: len(text.split())), None
    from src.embedder import Embedder

    embedder = Embedder(model_name=model_name)
    return embedder.count_tokens, embedder.tokenizer


def texts_from_db(db_path: str, collection: str) -> dict[str, list[str]]:
    import chromadb

    client = chromadb.PersistentClient(path=db_path)
    result = {}
    for strategy in ("fixed", "structure"):
        coll = client.get_collection(f"{collection}_{strategy}")
        texts, offset = [], 0
        while True:
            batch = coll.get(limit=2000, offset=offset, include=["documents"])
            docs = batch.get("documents") or []
            if not docs:
                break
            texts.extend(docs)
            offset += len(docs)
        result[strategy] = texts
    return result


def texts_from_pdfs(pdf_dir: str, manifest: str, config: dict, tokenizer) -> dict[str, list[str]]:
    from src.chunker import fixed_size_chunks, structure_aware_chunks
    from src.cleaner import clean_pages
    from src.parser import parse_pdf

    with open(manifest, encoding="utf-8", newline="") as handle:
        doc_ids = [row["doc_id"] for row in csv.DictReader(handle)]
    fixed_cfg, struct_cfg = config["chunking"]["fixed"], config["chunking"]["structure"]
    out = {"fixed": [], "structure": []}
    for doc_id in doc_ids:
        pdf = Path(pdf_dir) / f"{doc_id}.pdf"
        if not pdf.exists():
            print(f"missing: {pdf}")
            continue
        pages = clean_pages(parse_pdf(pdf))
        out["fixed"] += [c["text"] for c in fixed_size_chunks(
            pages, fixed_cfg["chunk_size"], fixed_cfg["overlap"], tokenizer)]
        out["structure"] += [c["text"] for c in structure_aware_chunks(
            pages, struct_cfg["target_size"], struct_cfg["max_size"],
            struct_cfg["min_size"], tokenizer)]
        print(f"chunked {doc_id}")
    return out


def main() -> None:
    import yaml

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", choices=["db", "pdf"], default="db")
    parser.add_argument("--db-path", default="chroma_db")
    parser.add_argument("--collection", default="policylens_v1")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--tokenizer", choices=["model", "whitespace"], default="model")
    parser.add_argument("--output", default="eval/chunk_stats.csv")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    count_tokens, tokenizer = make_counter(args.tokenizer, config["embedding"]["model"])
    if args.source == "db":
        texts = texts_from_db(args.db_path, args.collection)
    else:
        texts = texts_from_pdfs(args.pdf_dir, args.manifest, config, tokenizer)

    rows = []
    for strategy, items in texts.items():
        row = {"strategy": strategy, "token_unit": "model_tokens" if args.tokenizer == "model" else "words",
               "source": args.source, **summarize(items, count_tokens)}
        rows.append(row)
        print(row)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(args.output, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
