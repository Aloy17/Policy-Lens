from typing import Any

import chromadb


class VectorStore:
    """Store and search PolicyLens embeddings using Chroma."""

    def __init__(
        self,
        path: str,
        collection_name: str,
    ) -> None:
        self.client = chromadb.PersistentClient(path=path)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> None:
        """Add embedded chunks to the collection."""
        if not chunks:
            return

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for index, chunk in enumerate(chunks):
            metadata = chunk["metadata"]

            chunk_id = (
                f"{metadata['doc_id']}_"
                f"{metadata['chunk_strategy']}_"
                f"{index}"
            )

            ids.append(chunk_id)
            documents.append(chunk["text"])
            embeddings.append(chunk["embedding"])
            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def count(self) -> int:
        """Return the number of stored chunks."""
        return self.collection.count()

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search the collection using a query embedding."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

    def delete_document(self, doc_id: str) -> None:
        """Delete all chunks belonging to a document."""
        self.collection.delete(
            where={"doc_id": doc_id}
        )
