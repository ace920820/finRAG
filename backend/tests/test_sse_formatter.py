from app.core.sse import format_sse_error, format_sse_event, format_sse_ping, split_markdown_chunks
from app.models.events import QueryRewriteEvent


def test_sse_event_formatter_serializes_payloads():
    payload = QueryRewriteEvent(original='a', expanded=['b'], sub_queries=['c'])
    event = format_sse_event('query_rewrite', payload)

    assert event.startswith('event: query_rewrite')
    assert '"original": "a"' in event
    assert event.endswith('\n\n')


def test_ping_and_error_frames_are_deterministic():
    assert format_sse_ping() == 'event: ping\ndata: {}\n\n'
    error = format_sse_error('ERR', 'failed')
    assert 'event: error' in error
    assert '"code": "ERR"' in error


def test_markdown_chunking_preserves_paragraphs():
    chunks = split_markdown_chunks('### A\n\n- one\n\n- two', max_length=8)
    assert chunks
    assert all(chunk for chunk in chunks)
