"""Embedding adapter for OpenRouter's OpenAI-compatible API."""
import os
from typing import Protocol

from dotenv import load_dotenv


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Call a real OpenRouter embedding model; never fall back to fake vectors."""

    KNOWN_DIMENSIONS = {
        "openai/text-embedding-3-small": 1536,
        "text-embedding-3-small": 1536,
        "openai/text-embedding-3-large": 3072,
        "text-embedding-3-large": 3072,
    }

    def __init__(self, model_name: str, *, client=None, api_key: str | None = None,
                 dimensions: int | None = None) -> None:
        load_dotenv()
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "")
        if not self.model_name:
            raise ValueError("EMBEDDING_MODEL is required")
        key = api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY", "")
        if client is None and not key:
            raise RuntimeError("OPENROUTER_API_KEY is required; refusing mock embeddings")
        self.client = client or self._create_client(key)
        self.dimensions = dimensions or self.KNOWN_DIMENSIONS.get(self.model_name)
        if not self.dimensions:
            configured = os.getenv("EMBEDDING_DIMENSIONS", "")
            if not configured:
                raise ValueError("Set EMBEDDING_DIMENSIONS for this embedding model")
            self.dimensions = int(configured)

    @staticmethod
    def _create_client(api_key: str):
        from openai import OpenAI
        return OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={"HTTP-Referer": "https://openrouter.ai", "X-Title": "Day6 Data Ingestion"},
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model_name, input=texts)
        data = sorted(response.data, key=lambda item: item.index)
        vectors = [list(item.embedding) for item in data]
        if len(vectors) != len(texts):
            raise RuntimeError("Embedding provider returned an unexpected number of vectors")
        if any(len(vector) != self.dimensions for vector in vectors):
            raise RuntimeError("Embedding dimension does not match configured model dimension")
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, question: str) -> list[float]:
        vectors = self._embed([question])
        return vectors[0]
