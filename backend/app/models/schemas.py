from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


DocType = Literal["financial_report", "research_report", "news"]
QueryIntent = Literal["factual", "analytical", "reasoning"]
ScoreSource = Literal["rerank", "hybrid_fusion", "mock"]


class Document(BaseModel):
    doc_id: str
    company: str
    company_aliases: list[str] = Field(default_factory=list)
    doc_type: DocType
    title: str
    date: str
    source: str
    content: str


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    section: str
    page_num: Optional[int] = None
    chunk_index: int
    content: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentListItem(BaseModel):
    doc_id: str
    title: str
    doc_type: DocType
    company: str
    date: str
    chunk_count: int
    source: Optional[str] = None


class DocumentListResponse(BaseModel):
    total: int
    documents: list[DocumentListItem]


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    session_id: Optional[str] = None


class RetrievalResultItem(BaseModel):
    chunk_id: str
    title: str
    doc_type: DocType
    company: str
    date: str
    page: Optional[int] = None
    preview: str
    score: float


class RerankResultItem(BaseModel):
    chunk_id: str
    rank: int
    rerank_score: Optional[float] = None
    fusion_score: Optional[float] = None
    relevance_score: Optional[float] = None
    degraded: bool = False
    fallback_reason: Optional[str] = None
    score_source: ScoreSource = "rerank"
    title: str
    doc_type: DocType
    company: str
    date: str
    page: Optional[int] = None
    content: str
    citation_id: int


class CitationMetadata(BaseModel):
    chunk_id: str
    title: str
    doc_type: DocType
    company: str
    date: str
    page: Optional[int] = None
    source: Optional[str] = None
    section: Optional[str] = None
