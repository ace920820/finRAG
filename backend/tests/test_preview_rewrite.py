from fastapi.testclient import TestClient

from app.core.agent.query_analysis import detect_entities
from app.main import create_app


def test_detect_entities_for_demo_companies():
    assert detect_entities('贵州茅台 2023 年营业收入是多少？') == ['贵州茅台']
    assert detect_entities('CATL 近期有哪些风险？') == ['宁德时代']
    assert detect_entities('未知公司情况如何？') == []


def test_preview_rewrite_endpoint_returns_expansion_and_entities():
    client = TestClient(create_app())
    response = client.post('/api/preview-rewrite', json={'query': '宁德时代近期有哪些潜在经营风险？'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['original'].startswith('宁德时代')
    assert 'CATL' in payload['expanded_terms']
    assert '经营风险' in payload['expanded_terms']
    assert payload['detected_entities'] == ['宁德时代']
    assert payload['intent'] == 'analytical'
    assert payload['sub_queries']


def test_preview_rewrite_endpoint_rejects_empty_query():
    client = TestClient(create_app())
    response = client.post('/api/preview-rewrite', json={'query': ''})

    assert response.status_code == 422
