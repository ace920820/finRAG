from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Protocol, Sequence


@dataclass(frozen=True)
class ProviderResult:
    score: float
    metadata: dict[str, Any]


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        ...


class RerankProvider(Protocol):
    def rerank(self, query: str, documents: Sequence[str]) -> List[ProviderResult]:
        ...


class TextProvider(Protocol):
    def generate_text(self, prompt: str) -> str:
        ...
