from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


DocType = Literal["financial_report", "research_report", "news"]
QueryIntent = Literal["factual", "analytical", "reasoning"]
QueryTaskType = Literal[
    "metric_lookup",
    "causal_analysis",
    "risk_analysis",
    "trend_analysis",
    "comparison",
    "general_analysis",
]
RetrievalStrategy = Literal[
    "table_fact_first",
    "financial_report_first",
    "research_report_analysis",
    "general_hybrid",
]
ScoreSource = Literal["rerank", "hybrid_fusion", "mock"]


class QueryEntity(BaseModel):
    canonical: str
    aliases: list[str] = Field(default_factory=list)
    match: str


class QueryMetric(BaseModel):
    canonical: str
    aliases: list[str] = Field(default_factory=list)
    match: str


class QueryTimeRange(BaseModel):
    year: Optional[int] = None
    quarter: Optional[Literal["q1", "q2", "q3", "q4"]] = None
    fiscal: bool = False
    relative: Optional[Literal["latest", "recent", "recent_years"]] = None
    raw: Optional[str] = None


class RetrievalPlan(BaseModel):
    original_query: str
    normalized_query: str
    intent: QueryIntent
    task_type: QueryTaskType
    entities: list[QueryEntity] = Field(default_factory=list)
    metrics: list[QueryMetric] = Field(default_factory=list)
    time_range: Optional[QueryTimeRange] = None
    preferred_doc_types: list[DocType] = Field(default_factory=list)
    retrieval_strategy: RetrievalStrategy = "general_hybrid"
    filters: dict[str, Any] = Field(default_factory=dict)
    signals: list[str] = Field(default_factory=list)


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
    content: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


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
    metadata: dict[str, Any] = Field(default_factory=dict)


class CitationMetadata(BaseModel):
    chunk_id: str
    title: str
    doc_type: DocType
    company: str
    date: str
    page: Optional[int] = None
    source: Optional[str] = None
    section: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


KBStatus = Literal["ready", "importing", "failed", "not_initialized"]
KBDocumentStatus = Literal["active", "disabled", "failed"]


class KBOverviewResponse(BaseModel):
    total_documents: int
    total_chunks: int
    last_import_at: Optional[str] = None
    last_reindex_at: Optional[str] = None
    status: KBStatus


class KBDocumentListItem(BaseModel):
    doc_id: str
    title: str
    company: str
    doc_type: DocType
    date: str
    source: Optional[str] = None
    source_path: str = ""
    chunk_count: int
    status: KBDocumentStatus = "active"
    collection_name: str = "default"
    error_message: Optional[str] = None


class KBDocumentListResponse(BaseModel):
    total: int
    documents: list[KBDocumentListItem]


class KBChunkSummary(BaseModel):
    chunk_id: str
    chunk_index: int
    section: str = ""
    page_num: Optional[int] = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class KBDocumentDetail(KBDocumentListItem):
    chunks: list[KBChunkSummary] = Field(default_factory=list)


ImportJobStatus = Literal["pending", "running", "completed", "failed"]
ReindexStatus = Literal["not_requested", "running", "completed", "failed"]


class KBUploadResponse(BaseModel):
    uploaded: int
    saved_paths: list[str]


class KBImportRequest(BaseModel):
    collection_name: str = "default"
    source_dir: Optional[str] = None
    processed_dir: Optional[str] = None
    rebuild_index: bool = False
    default_company: str = "未知"
    default_doc_type: DocType = "research_report"
    default_date: str = "unknown"


class KBImportJobResponse(BaseModel):
    job_id: str
    status: ImportJobStatus
    total_files: int = 0
    success_count: int = 0
    fail_count: int = 0
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_messages: list[str] = Field(default_factory=list)
    reindex_status: ReindexStatus = "not_requested"


class KBReindexResponse(BaseModel):
    status: Literal["completed"]
