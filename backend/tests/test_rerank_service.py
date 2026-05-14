from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.models.schemas import RetrievalResultItem


class FailingRerankProvider:
    def rerank(self, query, documents):
        raise RuntimeError('rerank unavailable')


class CapturingRerankProvider:
    def __init__(self):
        self.documents = []

    def rerank(self, query, documents):
        self.documents = documents
        return []


def test_rerank_service_returns_top5_with_citation_ids():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    retrieval = retriever.retrieve('宁德时代 经营风险')
    result = RerankService().rerank('宁德时代 经营风险', retrieval.fused_top20)

    assert result.top5
    assert len(result.top5) <= 5
    assert result.top5[0].citation_id == 1
    assert result.degraded is False
    assert result.score_source == 'mock'
    assert result.top5[0].score_source == 'mock'
    assert result.top5[0].rerank_score is not None
    assert result.top5[0].fusion_score is None


def test_rerank_service_falls_back_on_failure():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    retrieval = retriever.retrieve('贵州茅台 营业收入')
    result = RerankService(FailingRerankProvider()).rerank('贵州茅台 营业收入', retrieval.fused_top20)

    assert result.degraded is True
    assert result.fallback_reason == 'rerank unavailable'
    assert result.top5
    assert result.score_source == 'hybrid_fusion'
    assert result.top5[0].score_source == 'hybrid_fusion'
    assert result.top5[0].degraded is True
    assert result.top5[0].fallback_reason == 'rerank unavailable'
    assert result.top5[0].rerank_score is None
    assert result.top5[0].relevance_score is None
    assert result.top5[0].fusion_score == retrieval.fused_top20[0].score


def test_rerank_service_sends_bounded_context_not_preview_only():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    retrieval = retriever.retrieve('宁德时代 经营风险')
    provider = CapturingRerankProvider()

    RerankService(provider).rerank('宁德时代 经营风险', retrieval.fused_top20)

    assert provider.documents
    assert provider.documents[0].startswith('标题：')
    assert '公司：' in provider.documents[0]
    assert '内容：' in provider.documents[0]
    assert len(provider.documents[0]) <= 1200


def test_rerank_alignment_penalizes_table_fact_when_requested_year_mismatches():
    candidate = RetrievalResultItem(
        chunk_id='fact-2026',
        title='NVDA FY2026Q3',
        doc_type='financial_report',
        company='NVIDIA',
        date='2025-11-19',
        preview='Table fact: Revenue = 57,006 | period: FY2026 Q3',
        score=1.0,
        content='Table fact: Revenue = 57,006 | period: FY2026 Q3',
        metadata={
            'chunk_type': 'table_fact',
            'metric': 'revenue',
            'period_label': 'FY2026 Q3',
            'source': 'NVDA_nvidia_10q_FY2026Q3_2025-11-19.pdf',
            'fact_reasons': ['company', 'metric', 'source_year:2026'],
        },
    )

    boost = RerankService._query_alignment_boost('英伟达2024年第三季度的总营收是多少？', candidate)

    assert boost < 0
