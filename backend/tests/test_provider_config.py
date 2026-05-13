from app.core.config import Settings, get_settings
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.providers.rerank import BailianRerankProvider, MockRerankProvider


def test_provider_config_defaults_are_offline_safe():
    settings = get_settings()
    assert settings.embedding_provider == 'mock'
    assert settings.rerank_provider == 'mock'
    assert settings.text_provider == 'mock'
    assert settings.model_api_key is None
    assert settings.rrf_k == 60
    assert settings.rerank_top_k == 5
    assert settings.rerank_base_url.endswith('/api/v1/services/rerank/text-rerank/text-rerank')


def test_provider_config_can_be_overridden():
    settings = Settings(
        model_api_key='test-key',
        embedding_provider='bailian',
        rerank_provider='bailian',
        text_provider='bailian',
        embedding_model='custom-embedding',
        rerank_model='custom-rerank',
        text_model='qwen-plus',
    )
    assert settings.model_api_key == 'test-key'
    assert settings.embedding_model == 'custom-embedding'
    assert settings.rerank_model == 'custom-rerank'
    assert settings.text_model == 'qwen-plus'


def test_mock_embedding_provider_is_deterministic():
    provider = MockEmbeddingProvider()
    first = provider.embed_texts(['贵州茅台', '宁德时代'])
    second = provider.embed_texts(['贵州茅台', '宁德时代'])
    assert first == second
    assert len(first) == 2


def test_mock_rerank_provider_is_deterministic():
    provider = MockRerankProvider()
    first = provider.rerank('宁德时代风险', ['原材料价格波动', '营业收入增长'])
    second = provider.rerank('宁德时代风险', ['原材料价格波动', '营业收入增长'])
    assert first == second
    assert first[0].score >= first[-1].score


def test_bailian_rerank_provider_uses_dashscope_rerank_endpoint(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {'output': {'results': [{'index': 1, 'relevance_score': 0.9}]}}

    def fake_post(url, json, headers, timeout):
        captured['url'] = url
        captured['json'] = json
        captured['headers'] = headers
        captured['timeout'] = timeout
        return Response()

    monkeypatch.setattr('app.core.providers.rerank.httpx.post', fake_post)
    provider = BailianRerankProvider(api_key='test-key')
    results = provider.rerank('query', ['doc a', 'doc b'])

    assert captured['url'].endswith('/api/v1/services/rerank/text-rerank/text-rerank')
    assert captured['json']['input']['query'] == 'query'
    assert captured['json']['input']['documents'] == ['doc a', 'doc b']
    assert captured['json']['parameters']['top_n'] == 5
    assert captured['headers']['Authorization'] == 'Bearer test-key'
    assert results[0].score == 0.9
    assert results[0].metadata['index'] == 1


def test_vector_search_uses_active_embedding_provider(monkeypatch):
    from app.core.retrieval.vector_store import VectorStore
    from app.models.schemas import Chunk

    class ActiveProvider:
        def embed_texts(self, texts):
            return [[0.0, 1.0] for _ in texts]

    chunk = Chunk(chunk_id='c1', doc_id='d1', section='s', chunk_index=0, content='hello', metadata={})
    store = VectorStore([chunk], [[0.0, 1.0]])
    monkeypatch.setattr('app.core.retrieval.vector_store.build_embedding_provider', lambda: ActiveProvider())

    results = store.search('query')

    assert results[0].chunk_id == 'c1'
    assert results[0].score == 1.0
