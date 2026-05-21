import json

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.schemas import RetrievalResultItem


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
    assert rewrite['plan']['retrieval_strategy'] == 'research_report_analysis'

    retrieval = _event(events, 'retrieval_complete')
    assert retrieval['bm25_results']
    assert retrieval['fused_top20']
    assert [stage['name'] for stage in retrieval['cascade_trace']] == [
        'query_plan',
        'metadata_filter',
        'coarse_recall',
        'fusion',
    ]

    rerank = _event(events, 'rerank_complete')
    assert rerank['top5']
    assert [stage['name'] for stage in rerank['cascade_trace']] == ['rerank', 'final_evidence']
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


def test_query_endpoint_exposes_plan_without_changing_event_order():
    client = TestClient(create_app())
    response = client.post('/api/query', json={'query': '宁德时代近期有哪些潜在经营风险？'})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    event_names = [name for name, _ in events]
    assert event_names[:4] == ['query_rewrite', 'intent_detected', 'retrieval_complete', 'rerank_complete']

    rewrite = _event(events, 'query_rewrite')
    assert rewrite['plan']['retrieval_strategy'] == 'research_report_analysis'



def test_query_endpoint_exposes_vector_retrieval_error(monkeypatch):
    class FakeRetrievalResult:
        bm25_results = []
        vector_results = []
        fused_top20 = []
        bm25_error = None
        vector_error = "Vector index dimension mismatch"

    class FakeRetriever:
        def retrieve(self, query):
            return FakeRetrievalResult()

    monkeypatch.setattr("app.api.query.HybridRetriever.load_default", lambda: FakeRetriever())

    client = TestClient(create_app())
    response = client.post('/api/query', json={'query': '贵州茅台最新的营收数据'})

    assert response.status_code == 200
    retrieval = _event(_parse_sse(response.text), 'retrieval_complete')
    assert retrieval['vector_results'] == []
    assert retrieval['vector_error'] == "Vector index dimension mismatch"
    assert retrieval['cascade_trace'] == []

def test_query_endpoint_rejects_invalid_body():
    client = TestClient(create_app())
    response = client.post('/api/query', json={'query': ''})

    assert response.status_code == 422


def test_query_endpoint_returns_table_fact_metadata_for_nvidia_revenue(monkeypatch):
    table_fact = RetrievalResultItem(
        chunk_id="fact-nvda-q3-revenue",
        title="NVDA_nvidia_10q_FY2026Q3_2025-11-19.pdf",
        doc_type="financial_report",
        company="NVIDIA",
        date="2025-11-19",
        page=21,
        preview="Table fact: Revenue = 57,006",
        score=0.9,
        content="Table fact: Revenue = 57,006 | period: FY2026 Q3 three months ended",
        metadata={
            "chunk_type": "table_fact",
            "metric": "revenue",
            "raw_value": "57,006",
            "table_id": "tbl-income",
            "fact_reasons": ["strict_period_match", "current_period", "period_year:2026"],
        },
    )

    class FakeRetrievalResult:
        bm25_results = [table_fact]
        vector_results = [table_fact]
        fused_top20 = [table_fact]

    class FakeRetriever:
        def retrieve(self, query):
            return FakeRetrievalResult()

    monkeypatch.setattr("app.api.query.HybridRetriever.load_default", lambda: FakeRetriever())

    client = TestClient(create_app())
    response = client.post('/api/query', json={'query': '英伟达2026年第三季度的总营收是多少？'})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    rerank = _event(events, 'rerank_complete')
    top = rerank['top5'][0]
    assert [stage['name'] for stage in rerank['cascade_trace']] == ['rerank', 'final_evidence']
    assert top['metadata']['chunk_type'] == 'table_fact'
    assert top['metadata']['metric'] == 'revenue'
    assert top['metadata']['raw_value'] == '57,006'

    answer_text = ''.join(payload['text'] for name, payload in events if name == 'answer_chunk')
    assert '57,006' in answer_text
    assert '<span class="cite" data-id="1">[1]</span>' in answer_text

    done = _event(events, 'done')
    citation = done['citations']['1']
    assert citation['metadata']['chunk_type'] == 'table_fact'
    assert citation['metadata']['table_id']
    assert citation['metadata']['raw_value'] == '57,006'


def test_query_endpoint_exposes_retrieval_channel_errors(monkeypatch):
    table_fact = RetrievalResultItem(
        chunk_id="fact-moutai-q1-revenue",
        title="600519SH_moutai_quarterly_report_2026Q1_2026-04-25_cninfo.pdf",
        doc_type="financial_report",
        company="贵州茅台",
        date="2026-04-25",
        page=1,
        preview="Table fact: 一、营业总收入 = 54,702,912,385.23",
        score=0.9,
        content="Table fact: 一、营业总收入 = 54,702,912,385.23 | period: 2026年第一季度",
        metadata={"chunk_type": "table_fact", "metric": "revenue", "raw_value": "54,702,912,385.23"},
    )

    class FakeRetrievalResult:
        bm25_results = [table_fact]
        vector_results = []
        fused_top20 = [table_fact]
        bm25_error = None
        vector_error = "Vector index dimension mismatch: query=1024, index=8"

    class FakeRetriever:
        def retrieve(self, query):
            return FakeRetrievalResult()

    monkeypatch.setattr("app.api.query.HybridRetriever.load_default", lambda: FakeRetriever())

    client = TestClient(create_app())
    response = client.post('/api/query', json={'query': '贵州茅台最新的营收数据'})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    retrieval = _event(events, 'retrieval_complete')
    assert retrieval['vector_results'] == []
    assert retrieval['vector_error'] == "Vector index dimension mismatch: query=1024, index=8"
    assert retrieval['bm25_error'] is None
    assert retrieval['cascade_trace'] == []
