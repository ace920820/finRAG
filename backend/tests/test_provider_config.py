from app.core.config import Settings, get_settings
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.providers.rerank import MockRerankProvider


def test_provider_config_defaults_are_offline_safe():
    settings = get_settings()
    assert settings.embedding_provider == 'mock'
    assert settings.rerank_provider == 'mock'
    assert settings.text_provider == 'mock'
    assert settings.model_api_key is None
    assert settings.rrf_k == 60
    assert settings.rerank_top_k == 5


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
