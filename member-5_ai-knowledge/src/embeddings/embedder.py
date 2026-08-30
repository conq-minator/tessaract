"""Embedding client interfacing with ModelRegistry."""

from typing import List
from src.models.registry import registry


class Embedder:
    """Convenience wrapper for dense vector embeddings via ModelRegistry."""

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        result = await registry.embed(texts=texts)
        return result.embeddings

    async def embed_query(self, query: str) -> List[float]:
        result = await registry.embed(texts=[query])
        return result.embeddings[0] if result.embeddings else []


embedder = Embedder()
