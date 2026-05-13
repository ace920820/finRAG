import json

from fastapi.testclient import TestClient

from app.main import create_app


def _parse_sse(body: str):
    events = []
    for raw in body.strip().split('\n\n'):
        lines = raw.splitlines()
        event = None
        data = None
        for line in lines:
            if line.startswith('event: '):
                event = line[len('event: '):]
            elif line.startswith('data: '):
                data = line[len('data: '):]
        if event:
            events.append((event, json.loads(data or '{}')))
    return events


def _event(events, name):
    return next(payload for event_name, payload in events if event_name == name)


def test_query_endpoint_streams_expected_events():
    client = TestClient(create_app())
    response = client.post('/api/query', json={'query': '宁德时代近期有哪些潜在经营风险？'})

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    events = _parse_sse(response.text)
    event_names = [name for name, _ in events]

    assert event_names[:4] == ['query_rewrite', 'intent_detected', 'retrieval_complete', 'rerank_complete']
    assert 'ping' in event_names
    assert 'answer_chunk' in event_names
    assert event_names[-1] == 'done'

    rewrite = _event(events, 'query_rewrite')
    assert rewrite['original'].startswith('宁德时代')
    assert rewrite['expanded']

    retrieval = _event(events, 'retrieval_complete')
    assert retrieval['bm25_results']
    assert retrieval['vector_results']
    assert retrieval['fused_top20']

    rerank = _event(events, 'rerank_complete')
    assert rerank['top5']
    assert rerank['degraded'] is False
    assert rerank['score_source'] == 'mock'
    assert rerank['top5'][0]['citation_id'] == 1
    assert rerank['top5'][0]['score_source'] == 'mock'
    assert rerank['top5'][0]['degraded'] is False
    assert rerank['top5'][0]['rerank_score'] is not None
    assert rerank['top5'][0]['fusion_score'] is None

    answer_text = ''.join(payload['text'] for name, payload in events if name == 'answer_chunk')
    assert '<span class="cite" data-id="' in answer_text

    done = _event(events, 'done')
    assert done['latency_ms'] >= 1
    assert done['total_tokens'] >= 1
    assert '1' in done['citations']


def test_query_endpoint_rejects_invalid_body():
    client = TestClient(create_app())
    response = client.post('/api/query', json={'query': ''})

    assert response.status_code == 422
