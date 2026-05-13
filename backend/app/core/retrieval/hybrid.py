from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from app.core.config import get_settings
from app.core.providers.embeddings import build_embedding_provider
from app.core.retrieval.bm25_store import BM25Result, BM25Store
from app.core.retrieval.index_store import RetrievalIndexStore
from app.core.retrieval.vector_store import VectorResult, VectorStore
from app.models.schemas import RetrievalResultItem


@dataclass(frozen=True)
class HybridRetrievalResult:
    bm25_results: List[RetrievalResultItem]
    vector_results: List[RetrievalResultItem]
    fused_top20: List[RetrievalResultItem]


class HybridRetriever:
    def __init__(self, bm25_store: BM25Store, vector_store: VectorStore, rrf_k: int = 60):
        self.bm25_store = bm25_store
        self.vector_store = vector_store
        self.rrf_k = rrf_k
        self.settings = get_settings()

    @classmethod
    def from_chunks(cls, chunks, embedding_provider=None) -> "HybridRetriever":
        bm25_store = BM25Store.from_chunks(chunks)
        vector_store = VectorStore.from_chunks(chunks, embedding_provider or build_embedding_provider())
        return cls(bm25_store=bm25_store, vector_store=vector_store, rrf_k=get_settings().rrf_k)

    @classmethod
    def load_default(cls) -> "HybridRetriever":
        index_store = RetrievalIndexStore.load_or_build()
        return cls(index_store.bm25_store, index_store.vector_store, rrf_k=get_settings().rrf_k)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> HybridRetrievalResult:
        limit = top_k or self.settings.retrieval_top_k
        bm25_hits = self.bm25_store.search(query, top_k=limit)
        vector_hits = self.vector_store.search(query, top_k=limit)
        fused_hits = self._rrf_fuse(bm25_hits, vector_hits, top_k=limit)
        return HybridRetrievalResult(
            bm25_results=[self._to_result(hit, rank + 1) for rank, hit in enumerate(bm25_hits)],
            vector_results=[self._to_result(hit, rank + 1) for rank, hit in enumerate(vector_hits)],
            fused_top20=[self._to_result(hit, rank + 1) for rank, hit in enumerate(fused_hits)],
        )

    def _rrf_fuse(self, bm25_hits: Sequence[BM25Result], vector_hits: Sequence[VectorResult], top_k: int) -> List[dict]:
        scores: Dict[str, float] = {}
        payloads: Dict[str, dict] = {}
        for rank, hit in enumerate(bm25_hits, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank)
            payloads[hit.chunk_id] = self._hit_to_payload(hit)
        for rank, hit in enumerate(vector_hits, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank)
            payloads[hit.chunk_id] = self._hit_to_payload(hit)
        ranked_ids = sorted(scores.keys(), key=lambda chunk_id: scores[chunk_id], reverse=True)[:top_k]
        fused: List[dict] = []
        for chunk_id in ranked_ids:
            payload = dict(payloads[chunk_id])
            payload["score"] = round(scores[chunk_id], 6)
            fused.append(payload)
        return fused

    @staticmethod
    def _hit_to_payload(hit) -> dict:
        if isinstance(hit, dict):
            payload = dict(hit)
        else:
            payload = {
                "chunk_id": hit.chunk_id,
                "title": hit.title,
                "doc_type": hit.doc_type,
                "company": hit.company,
                "date": hit.date,
                "page": hit.page,
                "preview": hit.preview,
                "content": hit.content,
                "metadata": hit.metadata,
            }
        payload.setdefault("score", getattr(hit, "score", 0.0))
        return payload

    @staticmethod
    def _to_result(hit, rank: int) -> RetrievalResultItem:
        payload = HybridRetriever._hit_to_payload(hit)
        return RetrievalResultItem(
            chunk_id=payload["chunk_id"],
            title=payload["title"],
            doc_type=payload["doc_type"],
            company=payload["company"],
            date=payload["date"],
            page=payload["page"],
            preview=payload["preview"],
            score=float(payload.get("score", getattr(hit, "score", 0.0))),
        )
