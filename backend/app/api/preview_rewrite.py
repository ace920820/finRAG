from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.agent.query_analysis import analyze_query, detect_entities
from app.models.schemas import QueryIntent, QueryRequest

router = APIRouter(prefix="/api", tags=["query"])


class PreviewRewriteResponse(BaseModel):
    original: str
    expanded_terms: list[str] = Field(default_factory=list)
    sub_queries: list[str] = Field(default_factory=list)
    detected_entities: list[str] = Field(default_factory=list)
    intent: QueryIntent


@router.post("/preview-rewrite", response_model=PreviewRewriteResponse)
def preview_rewrite(request: QueryRequest) -> PreviewRewriteResponse:
    rewrite, intent = analyze_query(request.query)
    return PreviewRewriteResponse(
        original=rewrite.original,
        expanded_terms=rewrite.expanded,
        sub_queries=rewrite.sub_queries,
        detected_entities=detect_entities(request.query),
        intent=intent.intent,
    )
