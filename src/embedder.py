from typing import Any

from sentence_transformers import SentenceTransformer


class Embedder:
    """Generate local embeddings using Sentence Transformers."""

    def __init__(
        self,
        model_name: str,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings

        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=True,
        )

        return embeddings.tolist()

    def embed_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate embeddings and attach them to chunks."""
        texts = [chunk["text"] for chunk in chunks]

        embeddings = self.embed_texts(texts)

        enriched_chunks = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_data = chunk.copy()
            chunk_data["embedding"] = embedding
            enriched_chunks.append(chunk_data)

        return enriched_chunks

    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        return self.model.get_sentence_embedding_dimension()
