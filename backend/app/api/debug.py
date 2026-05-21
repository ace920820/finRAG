from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.agent.query_analysis import analyze_query
from app.core.agent.workflow import run_retrieval_pipeline
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.models.events import RerankCompleteEvent, RetrievalCompleteEvent
from app.models.schemas import IterativeRetrievalTrace, RetrievalCascadeStage

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
    iterative_trace: Optional[IterativeRetrievalTrace] = None
    degraded: bool = False
    fallback_reason: Optional[str] = None


@router.post("/retrieval", response_model=DebugRetrievalResponse)
def debug_retrieval(request: DebugRetrievalRequest) -> DebugRetrievalResponse:
    rewrite, _ = analyze_query(request.query)
    pipeline = run_retrieval_pipeline(
        request.query,
        rewrite,
        retriever=HybridRetriever.load_default(),
        rerank_service=RerankService(),
    )
    retrieval = pipeline.retrieval_complete
    rerank = pipeline.rerank_complete
    cascade_trace = retrieval.cascade_trace + rerank.cascade_trace
    first_step = retrieval.iterative_trace.steps[0] if retrieval.iterative_trace and retrieval.iterative_trace.steps else None
    return DebugRetrievalResponse(
        retrieval_complete=retrieval,
        rerank_complete=rerank,
        route=first_step.route if first_step else _stage_metadata(retrieval, "query_plan").get("route"),
        route_reason=_stage_metadata(retrieval, "query_plan").get("route_reason"),
        applied_filters=first_step.applied_filters if first_step else dict(_stage_metadata(retrieval, "metadata_filter").get("applied_filters", {}) or {}),
        filter_before_count=_stage_count(retrieval, "metadata_filter", "input_count"),
        filter_after_count=_stage_count(retrieval, "metadata_filter", "output_count"),
        filters_relaxed=_stage_degraded(retrieval, "metadata_filter"),
        filter_fallback_reason=_stage_fallback(retrieval, "metadata_filter"),
        cascade_trace=cascade_trace,
        iterative_trace=retrieval.iterative_trace,
        degraded=pipeline.degraded,
        fallback_reason=pipeline.fallback_reason,
    )


def _stage_metadata(retrieval: RetrievalCompleteEvent, name: str) -> dict[str, object]:
    for stage in retrieval.cascade_trace:
        if stage.name == name:
            return stage.metadata
    return {}


def _stage_count(retrieval: RetrievalCompleteEvent, name: str, field: str) -> Optional[int]:
    for stage in retrieval.cascade_trace:
        if stage.name == name:
            return getattr(stage, field)
    return None


def _stage_degraded(retrieval: RetrievalCompleteEvent, name: str) -> bool:
    for stage in retrieval.cascade_trace:
        if stage.name == name:
            return stage.degraded
    return False


def _stage_fallback(retrieval: RetrievalCompleteEvent, name: str) -> Optional[str]:
    for stage in retrieval.cascade_trace:
        if stage.name == name:
            return stage.fallback_reason
    return None
