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
    """Scan the full collection and select substantive passages across its page range."""
    count = collection.count()
    batch_size = 500
    all_records = []

    # Paginate through the full collection because insertion order can cluster
    # records from one document and hide useful examples from later documents.
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
            page_start = metadata.get("page_start")
            if len(passage) < 250 or not isinstance(page_start, (int, float)):
                continue

            all_records.append({
                "page_start": page_start,
                "has_section": bool(str(metadata.get("section_title") or "").strip()),
                "id": record_id,
                "record": {
                    "id": record_id,
                    "metadata": metadata,
                    "passage_preview": passage[:200],
                },
            })

    if not all_records:
        return []

    # Prefer section-labelled records when enough exist. For fixed-size chunks,
    # section_title may legitimately be empty, so page-spread sampling still applies.
    labelled = [item for item in all_records if item["has_section"]]
    candidates = labelled if len(labelled) >= sample_size else all_records
    candidates.sort(key=lambda item: (item["page_start"], item["id"]))

    take = min(sample_size, len(candidates))
    last = len(candidates) - 1
    indices = (
        [round(i * last / (take - 1)) for i in range(take)]
        if take > 1 else [last // 2]
    )
    return [candidates[index]["record"] for index in indices]


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
            "Samples are selected across page ranges; section_title is preserved as stored "
            "and may be empty for fixed-size chunks."
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
