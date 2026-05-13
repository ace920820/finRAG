from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService


def test_hybrid_retrieval_returns_separate_stage_outputs():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    result = retriever.retrieve('宁德时代 经营风险', top_k=20)

    assert result.bm25_results
    assert result.vector_results
    assert result.fused_top20
    first = result.fused_top20[0]
    assert first.chunk_id
    assert first.title
    assert first.preview


def test_rrf_fusion_is_deterministic():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    first = retriever.retrieve('贵州茅台 营业收入', top_k=20).fused_top20
    second = retriever.retrieve('贵州茅台 营业收入', top_k=20).fused_top20
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]


def test_nvidia_fy2026_q3_revenue_query_retrieves_income_statement():
    retrieval = HybridRetriever.load_default().retrieve('英伟达2026年第三季度的总营收是多少？')
    rerank = RerankService().rerank('英伟达2026年第三季度的总营收是多少？', retrieval.fused_top20)

    top_text = ' '.join(item.content for item in rerank.top5[:3])
    assert 'NVDA_nvidia_10q_FY2026Q3' in rerank.top5[0].title
    assert 'Revenue' in top_text and '57,006' in top_text
