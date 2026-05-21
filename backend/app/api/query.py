from __future__ import annotations

import time
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.agent.generator import AnswerGenerator
from app.core.agent.query_analysis import analyze_query
from app.core.agent.workflow import build_citations, estimate_tokens, retrieval_query
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.core.retrieval.trace import rerank_trace
from app.core.sse import format_sse_error, format_sse_event, format_sse_ping, split_markdown_chunks
from app.models.events import DoneEvent, RerankCompleteEvent, RetrievalCompleteEvent
from app.models.schemas import QueryRequest

router = APIRouter(prefix="/api", tags=["query"])
logger = logging.getLogger(__name__)


@router.post("/query")
def query(request: QueryRequest) -> StreamingResponse:
    def event_stream():
        started_at = time.perf_counter()
        try:
            rewrite, intent = analyze_query(request.query)
            logger.info("query analysis complete intent=%s", intent.intent)
            yield format_sse_event("query_rewrite", rewrite)
            yield format_sse_event("intent_detected", intent)

            retrieval_emitted = False
            rerank_emitted = False
            evidence = []
            try:
                logger.info("retrieval started")
                retriever = HybridRetriever.load_default()
                retrieval_query_text = retrieval_query(rewrite)
                try:
                    retrieval_result = retriever.retrieve(retrieval_query_text, plan=rewrite.plan)
                except TypeError:
                    retrieval_result = retriever.retrieve(retrieval_query_text)
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
                    bm25_error=getattr(retrieval_result, "bm25_error", None),
                    vector_error=getattr(retrieval_result, "vector_error", None),
                    cascade_trace=list(getattr(retrieval_result, "cascade_trace", []) or []),
                )
                yield format_sse_event("retrieval_complete", retrieval)
                retrieval_emitted = True

                logger.info("rerank started candidates=%d", len(retrieval_result.fused_top20))
                rerank_result = RerankService().rerank(request.query, retrieval_result.fused_top20)
                logger.info("rerank complete top=%d degraded=%s", len(rerank_result.top5), rerank_result.degraded)
                rerank = RerankCompleteEvent(
                    top5=rerank_result.top5,
                    degraded=rerank_result.degraded,
                    fallback_reason=rerank_result.fallback_reason,
                    score_source=rerank_result.score_source,
                    cascade_trace=rerank_trace(
                        len(retrieval_result.fused_top20),
                        len(rerank_result.top5),
                        rerank_result.degraded,
                        rerank_result.fallback_reason,
                    ),
                )
                evidence = rerank_result.top5
                yield format_sse_event("rerank_complete", rerank)
                rerank_emitted = True
            except Exception as exc:
                logger.exception("retrieval/rerank degraded")
                if not retrieval_emitted:
                    yield format_sse_event("retrieval_complete", RetrievalCompleteEvent())
                if not rerank_emitted:
                    yield format_sse_event("rerank_complete", RerankCompleteEvent(
                        degraded=True,
                        fallback_reason=str(exc),
                        score_source="hybrid_fusion",
                    ))
                yield format_sse_error("RETRIEVAL_DEGRADED", str(exc))

            logger.info("generation started evidence=%d", len(evidence))
            answer_text = AnswerGenerator().generate(request.query, intent, evidence)
            logger.info("generation complete chars=%d", len(answer_text))
            chunks = split_markdown_chunks(answer_text)
            yield format_sse_ping()
            for index, chunk in enumerate(chunks):
                yield format_sse_event("answer_chunk", {"text": chunk, "is_final": index == len(chunks) - 1})
            yield format_sse_event("done", DoneEvent(
                latency_ms=max(1, int((time.perf_counter() - started_at) * 1000)),
                total_tokens=estimate_tokens(answer_text),
                citations=build_citations(evidence),
            ))
        except Exception as exc:  # pragma: no cover - defensive route-level guard
            yield format_sse_error("QUERY_FAILED", str(exc))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
