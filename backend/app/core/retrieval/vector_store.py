from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, Sequence

import numpy as np

from app.core.providers.embeddings import MockEmbeddingProvider, build_embedding_provider
from app.models.schemas import Chunk


@dataclass(frozen=True)
class VectorResult:
    chunk_id: str
    score: float
    title: str
    doc_type: str
    company: str
    date: str
    page: Optional[int]
    preview: str
    content: str
    metadata: Dict[str, object]


class VectorStore:
    def __init__(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]):
        self.chunks = list(chunks)
        self.vectors = np.asarray(list(vectors), dtype=float) if vectors else np.zeros((0, 0), dtype=float)
        if self.vectors.size:
            norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.vectors = self.vectors / norms

    @classmethod
    def from_chunks(cls, chunks: Sequence[Chunk], embedding_provider=None) -> "VectorStore":
        provider = embedding_provider or MockEmbeddingProvider()
        vectors = provider.embed_texts([chunk.content for chunk in chunks])
        return cls(chunks, vectors)

    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunks": [chunk.model_dump() for chunk in self.chunks],
            "vectors": self.vectors.tolist(),
        }
        (index_dir / "vector_index.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, index_dir: Path) -> Optional["VectorStore"]:
        path = index_dir / "vector_index.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        chunks = [Chunk(**item) for item in payload.get("chunks", [])]
        vectors = payload.get("vectors", [])
        return cls(chunks, vectors)

    def search(self, query: str, top_k: int = 20, embedding_provider=None) -> List[VectorResult]:
        if not self.chunks or self.vectors.size == 0:
            return []
        provider = embedding_provider or build_embedding_provider()
        query_vector = np.asarray(provider.embed_texts([query])[0], dtype=float)
        if query_vector.size == 0:
            return []
        if query_vector.size != self.vectors.shape[1]:
            raise ValueError(
                f"Query embedding dimension {query_vector.size} does not match index dimension {self.vectors.shape[1]}. "
                "Rebuild the vector index with the active embedding provider."
            )
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            query_norm = 1.0
        query_vector = query_vector / query_norm
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            scores = self.vectors @ query_vector
        scores = np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)
        ranked = sorted(enumerate(scores.tolist()), key=lambda item: item[1], reverse=True)[:top_k]
        results: List[VectorResult] = []
        for index, score in ranked:
            chunk = self.chunks[index]
            metadata = dict(chunk.metadata)
            title = str(metadata.get("source", metadata.get("title", chunk.chunk_id)))
            results.append(
                VectorResult(
                    chunk_id=chunk.chunk_id,
                    score=float(score),
                    title=title,
                    doc_type=str(metadata.get("doc_type", "news")),
                    company=str(metadata.get("company", metadata.get("company_name", ""))),
                    date=str(metadata.get("date", "")),
                    page=chunk.page_num,
                    preview=chunk.content[:120],
                    content=chunk.content,
                    metadata=metadata,
                )
            )
        return results

    @staticmethod
    def fallback_from_chunks(chunks: Sequence[Chunk]) -> "VectorStore":
        provider = MockEmbeddingProvider()
        return VectorStore.from_chunks(chunks, provider)
