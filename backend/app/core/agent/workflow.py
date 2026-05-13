from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from app.core.agent.generator import AnswerGenerator
from app.core.agent.query_analysis import analyze_query
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.models.events import DoneEvent, IntentDetectedEvent, QueryRewriteEvent, RerankCompleteEvent, RetrievalCompleteEvent
from app.models.schemas import CitationMetadata, QueryRequest


@dataclass(frozen=True)
class QueryWorkflowResult:
    query_rewrite: QueryRewriteEvent
    intent_detected: IntentDetectedEvent
    retrieval_complete: RetrievalCompleteEvent
    rerank_complete: RerankCompleteEvent
    answer_text: str
    done: DoneEvent
    degraded: bool = False
    fallback_reason: Optional[str] = None


class QueryWorkflow:
    def __init__(self, retriever=None, rerank_service=None, generator=None):
        self.retriever = retriever or HybridRetriever.load_default()
        self.rerank_service = rerank_service or RerankService()
        self.generator = generator or AnswerGenerator()

    def run(self, request: QueryRequest) -> QueryWorkflowResult:
        started_at = time.perf_counter()
        rewrite, intent = analyze_query(request.query)
        retrieval = RetrievalCompleteEvent()
        rerank = RerankCompleteEvent()
        degraded = False
        fallback_reason = None
        evidence = []
        try:
            retrieval_result = self.retriever.retrieve(_retrieval_query(rewrite))
            retrieval = RetrievalCompleteEvent(
                bm25_results=retrieval_result.bm25_results,
                vector_results=retrieval_result.vector_results,
                fused_top20=retrieval_result.fused_top20,
            )
            rerank_result = self.rerank_service.rerank(request.query, retrieval_result.fused_top20)
            rerank = RerankCompleteEvent(top5=rerank_result.top5)
            degraded = rerank_result.degraded
            fallback_reason = rerank_result.fallback_reason
            evidence = rerank_result.top5
        except Exception as exc:
            degraded = True
            fallback_reason = str(exc)
        answer = self.generator.generate(request.query, intent, evidence)
        citations = _build_citations(evidence)
        done = DoneEvent(
            latency_ms=max(1, int((time.perf_counter() - started_at) * 1000)),
            total_tokens=_estimate_tokens(answer),
            citations=citations,
        )
        return QueryWorkflowResult(
            query_rewrite=rewrite,
            intent_detected=intent,
            retrieval_complete=retrieval,
            rerank_complete=rerank,
            answer_text=answer,
            done=done,
            degraded=degraded,
            fallback_reason=fallback_reason,
        )


def _retrieval_query(rewrite: QueryRewriteEvent) -> str:
    parts = [rewrite.original] + rewrite.expanded[:8] + rewrite.sub_queries[:2]
    return " ".join(part for part in parts if part)


def _build_citations(items) -> Dict[str, CitationMetadata]:
    citations: Dict[str, CitationMetadata] = {}
    for item in items:
        citations[str(item.citation_id)] = CitationMetadata(
            chunk_id=item.chunk_id,
            title=item.title,
            doc_type=item.doc_type,
            company=item.company,
            date=item.date,
            page=item.page,
            source=item.title,
            section=None,
        )
    return citations


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)
