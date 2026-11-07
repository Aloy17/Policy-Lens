from typing import Any

import chromadb


class VectorStore:
    """Store and search PolicyLens embeddings using Chroma cosine distance."""

    def __init__(self, path: str, collection_name: str) -> None:
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Upsert chunks with source-version-aware IDs."""
        if not chunks:
            return
        ids, documents, embeddings, metadatas = [], [], [], []
        for index, chunk in enumerate(chunks):
            metadata = chunk["metadata"]
            version = metadata["source_hash"][:12]
            chunk_id = f"{metadata['doc_id']}_{metadata['chunk_strategy']}_{version}_{index}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            embeddings.append(chunk["embedding"])
            metadatas.append(metadata)
        self.collection.upsert(ids=ids, documents=documents,
                               embeddings=embeddings, metadatas=metadatas)

    def count(self) -> int:
        return self.collection.count()

    def search(self, query_embedding: list[float], top_k: int = 5,
               where: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.collection.query(query_embeddings=[query_embedding],
                                     n_results=top_k, where=where)

    def delete_document(self, doc_id: str) -> None:
        self.collection.delete(where={"doc_id": doc_id})

    def delete_old_versions(self, doc_id: str, source_hash: str) -> None:
        """Remove stale versions only after new chunks have been stored."""
        self.collection.delete(where={"$and": [
            {"doc_id": doc_id},
            {"source_hash": {"$ne": source_hash}},
        ]})
