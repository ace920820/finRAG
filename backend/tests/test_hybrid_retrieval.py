from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.hybrid import HybridRetriever


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
