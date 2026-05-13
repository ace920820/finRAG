from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.models.events import RerankCompleteEvent, RetrievalCompleteEvent

router = APIRouter(prefix="/api/debug", tags=["debug"])


class DebugRetrievalRequest(BaseModel):
    query: str = Field(min_length=1)


class DebugRetrievalResponse(BaseModel):
    retrieval_complete: RetrievalCompleteEvent
    rerank_complete: RerankCompleteEvent
    degraded: bool = False
    fallback_reason: Optional[str] = None


@router.post("/retrieval", response_model=DebugRetrievalResponse)
def debug_retrieval(request: DebugRetrievalRequest) -> DebugRetrievalResponse:
    retrieval = HybridRetriever.load_default().retrieve(request.query)
    rerank = RerankService().rerank(request.query, retrieval.fused_top20)
    return DebugRetrievalResponse(
        retrieval_complete=RetrievalCompleteEvent(
            bm25_results=retrieval.bm25_results,
            vector_results=retrieval.vector_results,
            fused_top20=retrieval.fused_top20,
        ),
        rerank_complete=RerankCompleteEvent(
            top5=rerank.top5,
            degraded=rerank.degraded,
            fallback_reason=rerank.fallback_reason,
            score_source=rerank.score_source,
        ),
        degraded=rerank.degraded,
        fallback_reason=rerank.fallback_reason,
    )
