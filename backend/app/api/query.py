from __future__ import annotations

import time
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.agent.generator import AnswerGenerator
from app.core.agent.query_analysis import analyze_query
from app.core.agent.workflow import build_citations, estimate_tokens, run_retrieval_pipeline
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
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
            evidence_pack = None
            try:
                logger.info("retrieval started")
                pipeline = run_retrieval_pipeline(
                    request.query,
                    rewrite,
                    retriever=HybridRetriever.load_default(),
                    rerank_service=RerankService(),
                )
                yield format_sse_event("retrieval_complete", pipeline.retrieval_complete)
                retrieval_emitted = True
                evidence_pack = pipeline.evidence_pack
                evidence = pipeline.evidence
                yield format_sse_event("rerank_complete", pipeline.rerank_complete)
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
            answer_text = AnswerGenerator().generate(request.query, intent, evidence, evidence_pack=evidence_pack)
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
