from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService


class FailingRerankProvider:
    def rerank(self, query, documents):
        raise RuntimeError('rerank unavailable')


def test_rerank_service_returns_top5_with_citation_ids():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    retrieval = retriever.retrieve('宁德时代 经营风险')
    result = RerankService().rerank('宁德时代 经营风险', retrieval.fused_top20)

    assert result.top5
    assert len(result.top5) <= 5
    assert result.top5[0].citation_id == 1


def test_rerank_service_falls_back_on_failure():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    retrieval = retriever.retrieve('贵州茅台 营业收入')
    result = RerankService(FailingRerankProvider()).rerank('贵州茅台 营业收入', retrieval.fused_top20)

    assert result.degraded is True
    assert result.fallback_reason == 'rerank unavailable'
    assert result.top5
