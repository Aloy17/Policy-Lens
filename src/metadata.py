from pathlib import Path
from typing import Any
import hashlib


def calculate_file_hash(file_path: str | Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    file_path = Path(file_path)

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    return sha256.hexdigest()


def build_chunk_metadata(
    chunk: dict[str, Any],
    document: dict[str, Any],
    source_hash: str,
    chunk_strategy: str,
) -> dict[str, Any]:
    """Build metadata required for a PolicyLens chunk."""
    return {
        "doc_id": str(document["doc_id"]),
        "title": str(document["title"]),
        "issuer": str(document["issuer"]),
        "issue_date": str(document["issue_date"]),
        "page_start": int(chunk["page_start"]),
        "page_end": int(chunk["page_end"]),
        "section_title": str(chunk.get("section_title", "")),
        "source_hash": source_hash,
        "chunk_strategy": chunk_strategy,
        "ocr_used": bool(chunk.get("ocr_used", False)),
        "document_type": str(document.get("document_type", "")),
    }


def attach_metadata(
    chunks: list[dict[str, Any]],
    document: dict[str, Any],
    source_hash: str,
    chunk_strategy: str,
) -> list[dict[str, Any]]:
    """Attach metadata to every chunk."""
    enriched_chunks = []

    for chunk_index, chunk in enumerate(chunks):
        chunk_data = chunk.copy()

        metadata = build_chunk_metadata(
            chunk=chunk,
            document=document,
            source_hash=source_hash,
            chunk_strategy=chunk_strategy,
        )
        metadata["chunk_index"] = chunk_index
        metadata["chunk_count"] = len(chunks)
        chunk_data["metadata"] = metadata

        enriched_chunks.append(chunk_data)

    return enriched_chunks
