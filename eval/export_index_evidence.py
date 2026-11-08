"""Export a read-only snapshot of PolicyLens Chroma collections for submission evidence.

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
    """Prefer substantive passages with section metadata from beyond opening pages."""
    count = collection.count()
    candidate_limit = min(count, max(sample_size * 100, 500))
    candidates = collection.get(
        limit=candidate_limit,
        include=["metadatas", "documents"],
    )

    ranked = []
    for index, record_id in enumerate(candidates.get("ids", [])):
        metadata = (candidates.get("metadatas") or [])[index] or {}
        document = (candidates.get("documents") or [])[index] or ""
        page_start = metadata.get("page_start", 0)
        section_title = str(metadata.get("section_title") or "").strip()
        passage = " ".join(document.split())
        # Exclude opening-page contents/index fragments where possible.
        if len(passage) < 250 or not section_title or not isinstance(page_start, (int, float)) or page_start <= 2:
            continue
        ranked.append((page_start, record_id, metadata, passage))

    # Spread examples across the available page range instead of taking adjacent chunks.
    ranked.sort(key=lambda item: (item[0], item[1]))
    if len(ranked) > sample_size:
        last = len(ranked) - 1
        indices = [round(i * last / (sample_size - 1)) for i in range(sample_size)] if sample_size > 1 else [last // 2]
        ranked = [ranked[i] for i in indices]

    records = [
        {
            "id": record_id,
            "metadata": metadata,
            "passage_preview": passage[:200],
        }
        for _, record_id, metadata, passage in ranked
    ]

    # If the strict filter yields too few examples, fill from remaining substantive passages.
    if len(records) < sample_size:
        used_ids = {record["id"] for record in records}
        for index, record_id in enumerate(candidates.get("ids", [])):
            if record_id in used_ids:
                continue
            metadata = (candidates.get("metadatas") or [])[index] or {}
            document = (candidates.get("documents") or [])[index] or ""
            passage = " ".join(document.split())
            if len(passage) < 250:
                continue
            records.append({"id": record_id, "metadata": metadata, "passage_preview": passage[:200]})
            used_ids.add(record_id)
            if len(records) >= sample_size:
                break

    return records


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
