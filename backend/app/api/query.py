from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.agent.workflow import QueryWorkflow
from app.core.sse import format_sse_error, format_sse_event, format_sse_ping, split_markdown_chunks
from app.models.schemas import QueryRequest

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
def query(request: QueryRequest) -> StreamingResponse:
    workflow = QueryWorkflow()

    def event_stream():
        try:
            result = workflow.run(request)
            chunks = split_markdown_chunks(result.answer_text)
            yield format_sse_event("query_rewrite", result.query_rewrite)
            yield format_sse_event("intent_detected", result.intent_detected)
            yield format_sse_event("retrieval_complete", result.retrieval_complete)
            yield format_sse_event("rerank_complete", result.rerank_complete)
            yield format_sse_ping()
            for index, chunk in enumerate(chunks):
                yield format_sse_event("answer_chunk", {"text": chunk, "is_final": index == len(chunks) - 1})
            yield format_sse_event("done", result.done)
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
