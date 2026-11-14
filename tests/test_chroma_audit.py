import csv
from pathlib import Path

import pytest

import audit_chroma


def write_manifest(path: Path):
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["doc_id", "title"])
        writer.writeheader()
        writer.writerow({"doc_id": "doc-1", "title": "Document 1"})
        writer.writerow({"doc_id": "doc-2", "title": "Document 2"})


def chunk_metadata(doc_id, index, count=2, strategy="fixed", source_hash="abc123"):
    return {
        "doc_id": doc_id,
        "chunk_index": index,
        "chunk_count": count,
        "chunk_strategy": strategy,
        "source_hash": source_hash,
    }


def test_load_manifest_rejects_duplicate_document_ids(tmp_path):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("doc_id,title\ndoc-1,One\ndoc-1,Duplicate\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate doc_id"):
        audit_chroma.load_manifest(manifest)


def test_inspect_records_reports_complete_document_and_missing_document():
    manifest = {
        "doc-1": {"doc_id": "doc-1"},
        "doc-2": {"doc_id": "doc-2"},
    }
    records = {
        "ids": ["doc-1_fixed_abc123_0", "doc-1_fixed_abc123_1"],
        "metadatas": [
            chunk_metadata("doc-1", 0),
            chunk_metadata("doc-1", 1),
        ],
    }

    report = audit_chroma.inspect_records(
        records, manifest, {"doc-1": "abc123"}, "fixed"
    )

    assert report["documents"]["doc-1"]["status"] == "ok"
    assert report["documents"]["doc-2"]["issues"] == ["missing_document"]
    assert report["documents_with_issues"] == 1


def test_inspect_records_detects_duplicate_and_missing_indices():
    manifest = {"doc-1": {"doc_id": "doc-1"}}
    records = {
        "ids": ["doc-1_fixed_abc123_0", "doc-1_fixed_abc123_0"],
        "metadatas": [
            chunk_metadata("doc-1", 0),
            chunk_metadata("doc-1", 0),
        ],
    }

    report = audit_chroma.inspect_records(
        records, manifest, {"doc-1": "abc123"}, "fixed"
    )
    issues = report["documents"]["doc-1"]["issues"]

    assert "duplicate_chunk_index" in issues
    assert "missing_or_out_of_range_chunk_index" in issues
    assert "chunk_id_mismatch" not in issues


def test_inspect_records_detects_source_hash_mismatch():
    manifest = {"doc-1": {"doc_id": "doc-1"}}
    records = {
        "ids": ["old-version"],
        "metadatas": [chunk_metadata("doc-1", 0, count=1, source_hash="oldhash")],
    }

    report = audit_chroma.inspect_records(
        records, manifest, {"doc-1": "newhash"}, "fixed"
    )

    assert "source_hash_mismatch" in report["documents"]["doc-1"]["issues"]


def test_inspect_records_reports_orphan_document_ids():
    manifest = {"doc-1": {"doc_id": "doc-1"}}
    records = {
        "ids": ["orphan_fixed_abc123_0"],
        "metadatas": [chunk_metadata("orphan", 0, count=1)],
    }

    report = audit_chroma.inspect_records(records, manifest, {}, "fixed")

    assert report["orphan_doc_ids"] == ["orphan"]


def test_audit_refuses_to_create_missing_database(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest)
    db_path = tmp_path / "does-not-exist"

    monkeypatch.setattr(
        "sys.argv",
        [
            "audit_chroma.py",
            "--manifest", str(manifest),
            "--db-path", str(db_path),
        ],
    )

    with pytest.raises(SystemExit) as error:
        audit_chroma.main()

    assert error.value.code == 2
    assert not db_path.exists()
