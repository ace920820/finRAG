from app.models.events import AnswerChunkEvent, DoneEvent, ErrorEvent, PingEvent, QueryRewriteEvent
from app.models.schemas import Chunk, Document, DocumentListResponse, QueryRequest


def test_schema_models_serialize():
    document = Document(
        doc_id='d001',
        company='贵州茅台',
        company_aliases=['茅台'],
        doc_type='financial_report',
        title='贵州茅台 2023 年年度报告',
        date='2024-03-28',
        source='fixture',
        content='content',
    )
    chunk = Chunk(
        chunk_id='c001',
        doc_id='d001',
        section='主要会计数据',
        page_num=23,
        chunk_index=0,
        content='贵州茅台2023年营业收入1505.60亿元，同比增长19.0%。',
        embedding=[],
        metadata={'company': '贵州茅台'},
    )
    response = DocumentListResponse(total=1, documents=[])
    request = QueryRequest(query='宁德时代近期有哪些潜在经营风险？', session_id='session-1')
    events = [
        QueryRewriteEvent(original='a', expanded=['b'], sub_queries=['c']),
        AnswerChunkEvent(text='hello', is_final=False),
        DoneEvent(latency_ms=1, total_tokens=2),
        ErrorEvent(code='ERR', message='failed'),
        PingEvent(),
    ]
    assert document.doc_id == 'd001'
    assert chunk.chunk_id == 'c001'
    assert response.total == 1
    assert request.query.startswith('宁德时代')
    assert events[0].expanded == ['b']
