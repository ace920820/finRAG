from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import get_settings
from app.core.providers.rerank import MockRerankProvider, build_rerank_provider
from app.models.schemas import RerankResultItem, RetrievalResultItem


@dataclass(frozen=True)
class RerankServiceResult:
    top5: List[RerankResultItem]
    degraded: bool = False
    fallback_reason: Optional[str] = None


class RerankService:
    def __init__(self, rerank_provider=None, top_k: Optional[int] = None):
        self.rerank_provider = rerank_provider or build_rerank_provider()
        self.top_k = top_k or get_settings().rerank_top_k

    def rerank(self, query: str, candidates: List[RetrievalResultItem]) -> RerankServiceResult:
        try:
            provider_results = self.rerank_provider.rerank(query, [candidate.preview for candidate in candidates])
            index_to_score = {}
            for rank, provider_result in enumerate(provider_results):
                index = int(provider_result.metadata.get("index", rank))
                index_to_score[index] = provider_result.score
            ranked = sorted(
                enumerate(candidates),
                key=lambda item: index_to_score.get(item[0], item[1].score),
                reverse=True,
            )[: self.top_k]
            return RerankServiceResult(
                top5=[self._to_rerank_item(candidate, rank + 1, index_to_score.get(index, candidate.score)) for rank, (index, candidate) in enumerate(ranked)],
                degraded=False,
            )
        except Exception as exc:
            fallback = candidates[: self.top_k]
            return RerankServiceResult(
                top5=[self._to_rerank_item(candidate, rank + 1, candidate.score) for rank, candidate in enumerate(fallback)],
                degraded=True,
                fallback_reason=str(exc),
            )

    @staticmethod
    def _to_rerank_item(candidate: RetrievalResultItem, rank: int, score: float) -> RerankResultItem:
        return RerankResultItem(
            chunk_id=candidate.chunk_id,
            rank=rank,
            rerank_score=float(score),
            title=candidate.title,
            doc_type=candidate.doc_type,
            company=candidate.company,
            date=candidate.date,
            page=candidate.page,
            content=candidate.preview,
            citation_id=rank,
        )
