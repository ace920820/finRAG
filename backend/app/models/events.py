from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.schemas import CitationMetadata, QueryIntent, RerankResultItem, RetrievalResultItem, ScoreSource


class QueryRewriteEvent(BaseModel):
    original: str
    expanded: list[str] = Field(default_factory=list)
    sub_queries: list[str] = Field(default_factory=list)


class RetrievalCompleteEvent(BaseModel):
    bm25_results: list[RetrievalResultItem] = Field(default_factory=list)
    vector_results: list[RetrievalResultItem] = Field(default_factory=list)
    fused_top20: list[RetrievalResultItem] = Field(default_factory=list)
    bm25_error: Optional[str] = None
    vector_error: Optional[str] = None


class RerankCompleteEvent(BaseModel):
    top5: list[RerankResultItem] = Field(default_factory=list)
    degraded: bool = False
    fallback_reason: Optional[str] = None
    score_source: ScoreSource = "rerank"


class IntentDetectedEvent(BaseModel):
    intent: QueryIntent
    template: str


class AnswerChunkEvent(BaseModel):
    text: str
    is_final: bool = False


class DoneEvent(BaseModel):
    latency_ms: int
    total_tokens: int
    citations: dict[str, CitationMetadata] = Field(default_factory=dict)


class ErrorEvent(BaseModel):
    code: str
    message: str


class PingEvent(BaseModel):
    type: Literal["ping"] = "ping"
