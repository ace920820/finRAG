from fastapi.testclient import TestClient

from app.main import create_app


def test_debug_retrieval_endpoint_returns_retrieval_and_rerank_sections():
    client = TestClient(create_app())
    response = client.post('/api/debug/retrieval', json={'query': '宁德时代近期有哪些经营风险？'})
    assert response.status_code == 200
    payload = response.json()
    assert 'retrieval_complete' in payload
    assert 'rerank_complete' in payload
    assert payload['retrieval_complete']['bm25_results']
    assert payload['retrieval_complete']['vector_results']
    assert payload['retrieval_complete']['fused_top20']
    assert payload['rerank_complete']['top5']
