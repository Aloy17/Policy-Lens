""""Export a read-only snapshot of PolicyLens Chroma collections for submission evidence.

Example:
    python eval/export_index_evidence.py --db-path "dist/PolicyLens/PolicyLens Data/chroma_db"
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import chromadb
import yaml


def select_representative_records(collection, sample_size: int) -> list[dict]:
    """Scan collection pages and prefer substantive passages with section metadata."""
    count = collection.count()
    batch_size = 500
    ranked = []
    fallback = []

    # Paginate through the full collection: insertion order can cluster early records
    # from one document and otherwise hide useful examples from later documents.
    for offset in range(0, count, batch_size):
        batch = collection.get(
            limit=min(batch_size, count - offset),
            offset=offset,
            include=["metadatas", "documents"],
        )
        for index, record_id in enumerate(batch.get("ids", [])):
            metadata = (batch.get("metadatas") or [])[index] or {}
            document = (batch.get("documents") or [])[index] or ""
            passage = " ".join(document.split())
            if len(passage) < 250:
                continue

            record = {
                "id": record_id,
                "metadata": metadata,
                "passage_preview": passage[:200],
            }
            fallback.append(record)

            page_start = metadata.get("page_start", 0)
            section_title = str(metadata.get("section_title") or "").strip()
            if section_title and isinstance(page_start, (int, float)) and page_start > 2:
                ranked.append((page_start, record_id, record))

    # Spread examples across the page range, avoiding adjacent chunks.
    ranked.sort(key=lambda item: (item[0], item[1]))
    selected = []
    if ranked:
        take = min(sample_size, len(ranked))
        last = len(ranked) - 1
        indices = [round(i * last / (take - 1)) for i in range(take)] if take > 1 else [last // 2]
        selected = [ranked[i][2] for i in indices]

    # Fill any remaining slots with substantive passages from the full scan.
    used_ids = {record["id"] for record in selected}
    if len(selected) < sample_size:
        for record in fallback:
            if record["id"] in used_ids:
                continue
            selected.append(record)
            used_ids.add(record["id"])
            if len(selected) >= sample_size:
                break

    return selected


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
        "note": "Read-only collection counts and representative records; no index writes performed.",
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
