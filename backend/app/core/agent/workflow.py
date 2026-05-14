from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from app.core.agent.generator import AnswerGenerator
from app.core.agent.query_analysis import analyze_query
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.models.events import DoneEvent, IntentDetectedEvent, QueryRewriteEvent, RerankCompleteEvent, RetrievalCompleteEvent
from app.models.schemas import CitationMetadata, QueryRequest


logger = logging.getLogger(__name__)


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
        logger.info("query workflow started")
        rewrite, intent = analyze_query(request.query)
        logger.info("query analysis complete intent=%s", intent.intent)
        retrieval = RetrievalCompleteEvent()
        rerank = RerankCompleteEvent()
        degraded = False
        fallback_reason = None
        evidence = []
        try:
            logger.info("retrieval started")
            retrieval_result = self.retriever.retrieve(retrieval_query(rewrite))
            logger.info(
                "retrieval complete bm25=%d vector=%d fused=%d",
                len(retrieval_result.bm25_results),
                len(retrieval_result.vector_results),
                len(retrieval_result.fused_top20),
            )
            retrieval = RetrievalCompleteEvent(
                bm25_results=retrieval_result.bm25_results,
                vector_results=retrieval_result.vector_results,
                fused_top20=retrieval_result.fused_top20,
            )
            logger.info("rerank started candidates=%d", len(retrieval_result.fused_top20))
            rerank_result = self.rerank_service.rerank(request.query, retrieval_result.fused_top20)
            logger.info("rerank complete top=%d degraded=%s", len(rerank_result.top5), rerank_result.degraded)
            rerank = RerankCompleteEvent(
                top5=rerank_result.top5,
                degraded=rerank_result.degraded,
                fallback_reason=rerank_result.fallback_reason,
                score_source=rerank_result.score_source,
            )
            degraded = rerank_result.degraded
            fallback_reason = rerank_result.fallback_reason
            evidence = rerank_result.top5
        except Exception as exc:
            logger.exception("query retrieval/rerank failed")
            degraded = True
            fallback_reason = str(exc)
            rerank = RerankCompleteEvent(degraded=True, fallback_reason=fallback_reason, score_source="hybrid_fusion")
        logger.info("generation started evidence=%d", len(evidence))
        answer = self.generator.generate(request.query, intent, evidence)
        logger.info("generation complete chars=%d", len(answer))
        citations = build_citations(evidence)
        done = DoneEvent(
            latency_ms=max(1, int((time.perf_counter() - started_at) * 1000)),
            total_tokens=estimate_tokens(answer),
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


def retrieval_query(rewrite: QueryRewriteEvent) -> str:
    parts = [rewrite.original] + rewrite.expanded[:8] + rewrite.sub_queries[:2]
    return " ".join(part for part in parts if part)


def build_citations(items) -> Dict[str, CitationMetadata]:
    citations: Dict[str, CitationMetadata] = {}
    for item in items:
        citations[str(item.citation_id)] = CitationMetadata(
            chunk_id=item.chunk_id,
            title=item.title,
            doc_type=item.doc_type,
            company=item.company,
            date=item.date,
            page=item.page,
            source=str(item.metadata.get("source") or item.metadata.get("source_pdf_name") or item.title),
            section=str(item.metadata.get("section") or item.metadata.get("table_id") or "") or None,
            metadata=dict(item.metadata),
        )
    return citations


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)
