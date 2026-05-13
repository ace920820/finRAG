from __future__ import annotations

import hashlib
from typing import List, Sequence, Optional, Union

import httpx

from app.core.config import get_settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency fallback
    OpenAI = None


class MockEmbeddingProvider:
    def __init__(self, dimension: int = 8):
        self.dimension = dimension

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vector = []
            for index in range(self.dimension):
                start = index * 4
                chunk = digest[start:start + 4]
                number = int.from_bytes(chunk, "big", signed=False)
                vector.append((number % 1000) / 1000.0)
            vectors.append(vector)
        return vectors


class BailianEmbeddingProvider:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.model_base_url
        self.api_key = api_key if api_key is not None else settings.model_api_key
        self.model = model or settings.embedding_model
        self.timeout_seconds = settings.provider_timeout_seconds
        # Keep requests well under common OpenAI-compatible body limits (DashScope is 6 MiB).
        self.max_batch_items = 10
        self.max_batch_bytes = 2_000_000
        if not self.api_key:
            raise ValueError("Bailian embedding provider requires FINRAG_MODEL_API_KEY")
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=self.timeout_seconds) if OpenAI is not None else None

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        if self._client is None:
            raise RuntimeError("openai package unavailable for Bailian embedding provider")

        vectors: List[List[float]] = []
        for batch in self._iter_batches(list(texts)):
            response = self._client.embeddings.create(model=self.model, input=batch)
            items = sorted(response.data, key=lambda item: getattr(item, "index", 0))
            vectors.extend([list(item.embedding) for item in items])
        return vectors

    def _iter_batches(self, texts: list[str]):
        batch: list[str] = []
        batch_bytes = 0
        for text in texts:
            text_bytes = len(text.encode("utf-8"))
            if batch and (
                len(batch) >= self.max_batch_items
                or batch_bytes + text_bytes > self.max_batch_bytes
            ):
                yield batch
                batch = []
                batch_bytes = 0
            batch.append(text)
            batch_bytes += text_bytes
        if batch:
            yield batch


def build_embedding_provider() -> Union[MockEmbeddingProvider, BailianEmbeddingProvider]:
    settings = get_settings()
    if settings.embedding_provider == "bailian" and settings.model_api_key:
        return BailianEmbeddingProvider()
    return MockEmbeddingProvider()
