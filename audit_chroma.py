"""Read-only integrity audit for the two PolicyLens ChromaDB collections.

This tool never creates collections and never writes to ChromaDB. It refuses to
open a database path that does not already contain chroma.sqlite3.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "data" / "manifest.csv"
DEFAULT_PDF_DIR = ROOT / "data" / "pdfs"
DEFAULT_DB_PATH = ROOT / "chroma_db"
DEFAULT_FIXED = "policylens_v1_fixed"
DEFAULT_STRUCTURE = "policylens_v1_structure"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = csv.DictReader(source)
        if not rows.fieldnames or "doc_id" not in rows.fieldnames:
            raise ValueError(f"Manifest must contain a doc_id column: {path}")
        documents: dict[str, dict[str, str]] = {}
        for row in rows:
            doc_id = (row.get("doc_id") or "").strip()
            if not doc_id:
                raise ValueError("Manifest contains an empty doc_id")
            if doc_id in documents:
                raise ValueError(f"Manifest contains duplicate doc_id: {doc_id}")
            documents[doc_id] = row
    return documents


def inspect_records(
    records: dict[str, Any],
    manifest: dict[str, dict[str, str]],
    expected_hashes: dict[str, str],
    strategy: str,
) -> dict[str, Any]:
    ids = records.get("ids") or []
    metadatas = records.get("metadatas") or []
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    malformed_records: list[str] = []

    for record_id, metadata in zip(ids, metadatas):
        if not isinstance(metadata, dict):
            malformed_records.append(str(record_id))
            continue
        doc_id = metadata.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            malformed_records.append(str(record_id))
            continue
        grouped[doc_id].append((str(record_id), metadata))

    report: dict[str, Any] = {
        "strategy": strategy,
        "record_count": len(ids),
        "manifest_document_count": len(manifest),
        "documents": {},
        "orphan_doc_ids": sorted(set(grouped) - set(manifest)),
        "malformed_record_ids": malformed_records,
    }

    for doc_id in sorted(manifest):
        rows = grouped.get(doc_id, [])
        hashes = sorted({
            str(metadata.get("source_hash"))
            for _, metadata in rows
            if metadata.get("source_hash")
        })
        expected_hash = expected_hashes.get(doc_id)
        current_rows = [
            (record_id, metadata) for record_id, metadata in rows
            if expected_hash is None or metadata.get("source_hash") == expected_hash
        ]
        current_metadata = [metadata for _, metadata in current_rows]
        indices = [metadata.get("chunk_index") for metadata in current_metadata]
        counts = [metadata.get("chunk_count") for metadata in current_metadata]
        issues: list[str] = []

        if not rows:
            issues.append("missing_document")
        if expected_hash is not None and rows and expected_hash not in hashes:
            issues.append("source_hash_mismatch")
        if len(hashes) > 1:
            issues.append("multiple_source_versions")
        if rows and any(metadata.get("chunk_strategy") != strategy for _, metadata in rows):
            issues.append("wrong_strategy_metadata")

        if current_metadata:
            if any(type(count) is not int or count <= 0 for count in counts):
                issues.append("invalid_chunk_count")
            elif len(set(counts)) != 1:
                issues.append("inconsistent_chunk_count")
            else:
                expected_count = counts[0]
                valid_indices = [index for index in indices if type(index) is int]
                if len(valid_indices) != len(indices):
                    issues.append("invalid_chunk_index")
                if len(valid_indices) != len(set(valid_indices)):
                    issues.append("duplicate_chunk_index")
                if sorted(valid_indices) != list(range(expected_count)):
                    issues.append("missing_or_out_of_range_chunk_index")
                if len(current_metadata) != expected_count:
                    issues.append("record_count_mismatch")

                expected_prefix = f"{doc_id}_{strategy}_{(expected_hash or hashes[0])[:12]}_"
                for record_id, metadata in current_rows:
                    index = metadata.get("chunk_index")
                    if type(index) is int and record_id != f"{expected_prefix}{index}":
                        issues.append("chunk_id_mismatch")
                        break

        if expected_hash is None and rows:
            issues.append("local_pdf_missing_hash_unverified")
        report["documents"][doc_id] = {
            "records": len(rows),
            "current_version_records": len(current_rows),
            "source_hashes": hashes,
            "expected_source_hash": expected_hash,
            "status": "ok" if not issues else "issues",
            "issues": sorted(set(issues)),
        }

    report["documents_ok"] = sum(
        item["status"] == "ok" for item in report["documents"].values()
    )
    report["documents_with_issues"] = sum(
        item["status"] != "ok" for item in report["documents"].values()
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only integrity audit of existing PolicyLens ChromaDB indexes."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--fixed-collection", default=DEFAULT_FIXED)
    parser.add_argument("--structure-collection", default=DEFAULT_STRUCTURE)
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    pdf_dir = args.pdf_dir.expanduser().resolve()
    db_path = args.db_path.expanduser().resolve()

    if not manifest_path.is_file():
        parser.error(f"Manifest does not exist: {manifest_path}")
    if not db_path.is_dir() or not (db_path / "chroma.sqlite3").is_file():
        parser.error(
            f"Existing ChromaDB database not found at {db_path}; refusing to create it."
        )

    manifest = load_manifest(manifest_path)
    expected_hashes: dict[str, str] = {}
    missing_pdfs: list[str] = []
    for doc_id in manifest:
        pdf_path = pdf_dir / f"{doc_id}.pdf"
        if pdf_path.is_file():
            expected_hashes[doc_id] = sha256_file(pdf_path)
        else:
            missing_pdfs.append(doc_id)

    try:
        import chromadb
    except ImportError as error:
        parser.error(f"ChromaDB is not installed in this Python environment: {error}")

    client = chromadb.PersistentClient(path=str(db_path))
    existing_names = {
        item if isinstance(item, str) else item.name
        for item in client.list_collections()
    }
    output: dict[str, Any] = {
        "database_path": str(db_path),
        "manifest_path": str(manifest_path),
        "manifest_documents": len(manifest),
        "pdf_hashes_available": len(expected_hashes),
        "pdfs_missing": sorted(missing_pdfs),
        "collections": {},
        "collections_missing": [],
    }

    for strategy, collection_name in (
        ("fixed", args.fixed_collection),
        ("structure", args.structure_collection),
    ):
        if collection_name not in existing_names:
            output["collections_missing"].append(collection_name)
            output["collections"][strategy] = {
                "collection_name": collection_name,
                "status": "missing_collection",
                "record_count": 0,
            }
            continue
        collection = client.get_collection(name=collection_name)
        records = collection.get(include=["metadatas"])
        output["collections"][strategy] = {
            "collection_name": collection_name,
            **inspect_records(records, manifest, expected_hashes, strategy),
        }

    print(json.dumps(output, indent=2, sort_keys=True))
    has_issues = bool(output["collections_missing"] or missing_pdfs)
    has_issues = has_issues or any(
        collection.get("documents_with_issues", 0) > 0
        or collection.get("orphan_doc_ids")
        or collection.get("malformed_record_ids")
        for collection in output["collections"].values()
    )
    return 1 if has_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
