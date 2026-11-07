import os
import time
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer


class Embedder:
    """Generate local embeddings using Sentence Transformers."""

    def __init__(self, model_name: str, batch_size: int = 32,
                 normalize_embeddings: bool = True, retries: int = 3) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self.retries = retries
        model_path = os.environ.get("POLICYLENS_MODEL_PATH")
        if model_path:
            local_model = Path(model_path).expanduser().resolve()
            if not local_model.is_dir():
                raise FileNotFoundError(f"Embedding model not found: {local_model}")
            self.model = SentenceTransformer(str(local_model), local_files_only=True)
        else:
            self.model = SentenceTransformer(model_name)

    @property
    def tokenizer(self):
        return self.model.tokenizer

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        last_error = None
        for attempt in range(self.retries):
            try:
                embeddings = self.model.encode(
                    texts, batch_size=self.batch_size,
                    normalize_embeddings=self.normalize_embeddings,
                    show_progress_bar=True)
                return embeddings.tolist()
            except Exception as error:
                last_error = error
                if attempt + 1 < self.retries:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"Embedding failed after {self.retries} attempts") from last_error

    def embed_chunks(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        embeddings = self.embed_texts([chunk["text"] for chunk in chunks])
        enriched = []
        for chunk, embedding in zip(chunks, embeddings):
            item = chunk.copy()
            item["embedding"] = embedding
            enriched.append(item)
        return enriched

    def get_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
