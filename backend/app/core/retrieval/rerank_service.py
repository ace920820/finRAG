from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import get_settings
from app.core.providers.rerank import MockRerankProvider, build_rerank_provider
from app.models.schemas import RerankResultItem, RetrievalResultItem, ScoreSource


@dataclass(frozen=True)
class RerankServiceResult:
    top5: List[RerankResultItem]
    degraded: bool = False
    fallback_reason: Optional[str] = None
    score_source: ScoreSource = "rerank"


class RerankService:
    def __init__(self, rerank_provider=None, top_k: Optional[int] = None):
        self.rerank_provider = rerank_provider or build_rerank_provider()
        self.top_k = top_k or get_settings().rerank_top_k

    def rerank(self, query: str, candidates: List[RetrievalResultItem]) -> RerankServiceResult:
        try:
            score_source: ScoreSource = "mock" if isinstance(self.rerank_provider, MockRerankProvider) else "rerank"
            provider_results = self.rerank_provider.rerank(query, [self._format_rerank_document(candidate) for candidate in candidates])
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
                top5=[
                    self._to_rerank_item(
                        candidate,
                        rank + 1,
                        rerank_score=index_to_score.get(index, candidate.score),
                        score_source=score_source,
                    )
                    for rank, (index, candidate) in enumerate(ranked)
                ],
                degraded=False,
                score_source=score_source,
            )
        except Exception as exc:
            fallback = candidates[: self.top_k]
            return RerankServiceResult(
                top5=[
                    self._to_rerank_item(
                        candidate,
                        rank + 1,
                        fusion_score=candidate.score,
                        degraded=True,
                        fallback_reason=str(exc),
                        score_source="hybrid_fusion",
                    )
                    for rank, candidate in enumerate(fallback)
                ],
                degraded=True,
                fallback_reason=str(exc),
                score_source="hybrid_fusion",
            )

    @staticmethod
    def _to_rerank_item(
        candidate: RetrievalResultItem,
        rank: int,
        rerank_score: Optional[float] = None,
        fusion_score: Optional[float] = None,
        degraded: bool = False,
        fallback_reason: Optional[str] = None,
        score_source: ScoreSource = "rerank",
    ) -> RerankResultItem:
        return RerankResultItem(
            chunk_id=candidate.chunk_id,
            rank=rank,
            rerank_score=float(rerank_score) if rerank_score is not None else None,
            relevance_score=float(rerank_score) if rerank_score is not None and score_source == "rerank" else None,
            fusion_score=float(fusion_score) if fusion_score is not None else None,
            degraded=degraded,
            fallback_reason=fallback_reason,
            score_source=score_source,
            title=candidate.title,
            doc_type=candidate.doc_type,
            company=candidate.company,
            date=candidate.date,
            page=candidate.page,
            content=candidate.preview,
            citation_id=rank,
        )

    @staticmethod
    def _format_rerank_document(candidate: RetrievalResultItem, max_chars: int = 1200) -> str:
        parts = [
            f"标题：{candidate.title}",
            f"公司：{candidate.company}",
            f"类型：{candidate.doc_type}",
            f"日期：{candidate.date}",
        ]
        if candidate.page is not None:
            parts.append(f"页码：{candidate.page}")
        parts.append(f"内容：{candidate.preview}")
        return "\n".join(parts)[:max_chars]
