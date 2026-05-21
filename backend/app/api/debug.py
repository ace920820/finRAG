from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.agent.query_analysis import analyze_query
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.core.retrieval.trace import rerank_trace
from app.models.events import RerankCompleteEvent, RetrievalCompleteEvent
from app.models.schemas import RetrievalCascadeStage

router = APIRouter(prefix="/api/debug", tags=["debug"])


class DebugRetrievalRequest(BaseModel):
    query: str = Field(min_length=1)


class DebugRetrievalResponse(BaseModel):
    retrieval_complete: RetrievalCompleteEvent
    rerank_complete: RerankCompleteEvent
    route: Optional[str] = None
    route_reason: Optional[str] = None
    applied_filters: dict[str, object] = Field(default_factory=dict)
    filter_before_count: Optional[int] = None
    filter_after_count: Optional[int] = None
    filters_relaxed: bool = False
    filter_fallback_reason: Optional[str] = None
    cascade_trace: list[RetrievalCascadeStage] = Field(default_factory=list)
    degraded: bool = False
    fallback_reason: Optional[str] = None


@router.post("/retrieval", response_model=DebugRetrievalResponse)
def debug_retrieval(request: DebugRetrievalRequest) -> DebugRetrievalResponse:
    rewrite, _ = analyze_query(request.query)
    retrieval = HybridRetriever.load_default().retrieve(request.query, plan=rewrite.plan)
    rerank = RerankService().rerank(request.query, retrieval.fused_top20)
    retrieval_trace = list(getattr(retrieval, "cascade_trace", []) or [])
    rerank_stages = rerank_trace(len(retrieval.fused_top20), len(rerank.top5), rerank.degraded, rerank.fallback_reason)
    cascade_trace = retrieval_trace + rerank_stages
    return DebugRetrievalResponse(
        retrieval_complete=RetrievalCompleteEvent(
            bm25_results=retrieval.bm25_results,
            vector_results=retrieval.vector_results,
            fused_top20=retrieval.fused_top20,
            cascade_trace=retrieval_trace,
        ),
        rerank_complete=RerankCompleteEvent(
            top5=rerank.top5,
            degraded=rerank.degraded,
            fallback_reason=rerank.fallback_reason,
            score_source=rerank.score_source,
            cascade_trace=rerank_stages,
        ),
        route=getattr(retrieval, "route", None),
        route_reason=getattr(retrieval, "route_reason", None),
        applied_filters=dict(getattr(retrieval, "applied_filters", {}) or {}),
        filter_before_count=getattr(retrieval, "filter_before_count", None),
        filter_after_count=getattr(retrieval, "filter_after_count", None),
        filters_relaxed=getattr(retrieval, "filters_relaxed", False),
        filter_fallback_reason=getattr(retrieval, "filter_fallback_reason", None),
        cascade_trace=cascade_trace,
        degraded=rerank.degraded,
        fallback_reason=rerank.fallback_reason,
    )
