from app.core.agent.generator import build_mock_answer
from app.core.agent.query_analysis import analyze_query
from app.core.agent.workflow import QueryWorkflow
from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.models.schemas import QueryRequest


def _workflow():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    return QueryWorkflow(retriever=retriever, rerank_service=RerankService())


def test_mock_answer_contains_clickable_citation():
    workflow = _workflow()
    result = workflow.run(QueryRequest(query='贵州茅台 2023 年营业收入是多少？同比增长率？'))

    assert result.answer_text.startswith('###')
    assert '<span class="cite" data-id="' in result.answer_text
    assert result.done.citations
    assert '1' in result.done.citations


def test_workflow_returns_all_stage_payloads():
    workflow = _workflow()
    result = workflow.run(QueryRequest(query='宁德时代近期有哪些潜在经营风险？', session_id='s1'))

    assert result.query_rewrite.expanded
    assert result.intent_detected.intent == 'analytical'
    assert result.retrieval_complete.bm25_results
    assert result.retrieval_complete.vector_results
    assert result.retrieval_complete.fused_top20
    assert result.rerank_complete.top5
    assert result.rerank_complete.top5[0].citation_id == 1
    assert result.done.latency_ms >= 1
    assert result.done.total_tokens >= 1


def test_mock_answer_falls_back_when_no_evidence():
    _, intent = analyze_query('未知公司收入是多少？')

    assert build_mock_answer('未知公司收入是多少？', intent, []) == '资料中未提及。'
