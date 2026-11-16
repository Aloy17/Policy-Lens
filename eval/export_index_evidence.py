"""Export a read-only snapshot of PolicyLens Chroma collections for submission evidence.

Example:
    python eval/export_index_evidence.py --db-path "dist/PolicyLens/PolicyLens Data/chroma_db"
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import chromadb
import yaml


BOILERPLATE_PATTERNS = (
    "printed by the general manager",
    "published by the controller of publications",
    "government of india press",
    "all rights reserved",
    "table of contents",
    "contents",
)


def passage_quality(passage: str, metadata: dict) -> float:
    """Return a conservative readability/substance score in the 0..1 range."""
    text = " ".join(passage.split())
    if len(text) < 250:
        return 0.0

    chars = [char for char in text if not char.isspace()]
    if not chars:
        return 0.0

    ascii_letters = sum(char.isascii() and char.isalpha() for char in chars)
    alphabetic = sum(char.isalpha() for char in chars)
    tokens = re.findall(r"[A-Za-z]+", text)
    words = re.findall(r"\b\w+\b", text)
    if not tokens or not words:
        return 0.0

    latin_ratio = ascii_letters / max(alphabetic, 1)
    alpha_ratio = alphabetic / len(chars)
    token_ratio = len(tokens) / len(words)
    long_token_ratio = sum(len(token) <= 24 for token in tokens) / len(tokens)

    score = (
        0.35 * latin_ratio
        + 0.25 * alpha_ratio
        + 0.25 * token_ratio
        + 0.15 * long_token_ratio
    )

    lowered = text.lower()
    if any(phrase in lowered for phrase in BOILERPLATE_PATTERNS):
        score -= 0.45
    if re.search(r"(?:\\.\\s*){8,}", text) or text.count("_") > 12:
        score -= 0.2
    if metadata.get("ocr_used"):
        score -= 0.08
    if metadata.get("document_type") == "scanned_or_mixed":
        score -= 0.05

    section = str(metadata.get("section_title") or "").strip()
    if section and len(section) >= 8 and len(section.split()) >= 2:
        score += 0.04

    return max(0.0, min(1.0, score))


def select_representative_records(collection, sample_size: int) -> list[dict]:
    """Choose readable, substantive records while avoiding document duplication."""
    count = collection.count()
    batch_size = 500
    candidates = []

    for offset in range(0, count, batch_size):
        batch = collection.get(
            limit=min(batch_size, count - offset),
            offset=offset,
            include=["metadatas", "documents"],
        )
        metadatas = batch.get("metadatas") or []
        documents = batch.get("documents") or []
        for index, record_id in enumerate(batch.get("ids", [])):
            metadata = metadatas[index] or {}
            passage = " ".join((documents[index] or "").split())
            page_start = metadata.get("page_start")
            if len(passage) < 250 or not isinstance(page_start, (int, float)):
                continue

            quality = passage_quality(passage, metadata)
            if quality < 0.58 or page_start <= 2:
                continue

            candidates.append({
                "page_start": page_start,
                "doc_id": metadata.get("doc_id") or record_id,
                "quality": quality,
                "id": record_id,
                "record": {
                    "id": record_id,
                    "metadata": metadata,
                    "passage_preview": passage[:200],
                },
            })

    if not candidates:
        return []

    # Keep the strongest passage per source document before selecting the
    # page-spread sample. This prevents long PDFs dominating the evidence.
    best_by_document = {}
    for item in candidates:
        key = item["doc_id"]
        previous = best_by_document.get(key)
        if previous is None or (item["quality"], -item["page_start"], item["id"]) > (
            previous["quality"], -previous["page_start"], previous["id"]
        ):
            best_by_document[key] = item

    diversified = sorted(
        best_by_document.values(),
        key=lambda item: (item["page_start"], item["doc_id"], item["id"]),
    )
    take = min(sample_size, len(diversified))
    last = len(diversified) - 1
    indices = (
        [round(i * last / (take - 1)) for i in range(take)]
        if take > 1 else [last // 2]
    )
    selected = [diversified[index] for index in indices]
    return [item["record"] for item in selected]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=None,
                        help="Chroma persistence directory (defaults to config.yaml).")
    parser.add_argument("--fixed-collection", default="policylens_v1_fixed")
    parser.add_argument("--structure-collection", default="policylens_v1_structure")
    parser.add_argument("--output", default="evidence/index_snapshot")
    parser.add_argument("--sample-size", type=int, default=5)
    args = parser.parse_args()

    if args.sample_size < 1:
        parser.error("--sample-size must be at least 1")

    db_path = args.db_path
    if db_path is None:
        with Path("config.yaml").open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        db_path = config["vector_store"]["path"]

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(Path(db_path).expanduser()))

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_path": str(Path(db_path).expanduser()),
        "collections": {},
        "note": (
            "Read-only collection counts and representative records; no index writes performed. "
            "Samples prioritize readable substantive passages, exclude likely boilerplate and "
            "low-readability OCR text, use one record per source document where possible, "
            "and are spread across the available page range."
        ),
    }

    for name in (args.fixed_collection, args.structure_collection):
        collection = client.get_collection(name=name)
        records = select_representative_records(collection, args.sample_size)
        summary["collections"][name] = {
            "count": collection.count(),
            "sample_records": len(records),
            "records": records,
        }
        with (output / f"{name}_sample.json").open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2, ensure_ascii=False, default=str)

    with (output / "index_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False, default=str)

    print(f"Index evidence written to: {output.resolve()}")
    for name, details in summary["collections"].items():
        print(f"{name}: {details['count']:,} chunks; "
              f"{details['sample_records']} sample records exported")


if __name__ == "__main__":
    main()
