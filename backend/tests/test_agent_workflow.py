from app.core.agent.generator import build_mock_answer
from app.core.agent.query_analysis import analyze_query
from app.core.agent.workflow import QueryWorkflow
from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.hybrid import HybridRetrievalResult
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.models.schemas import RetrievalResultItem
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
    assert [stage.name for stage in result.retrieval_complete.cascade_trace] == [
        'query_plan',
        'coarse_recall',
        'metadata_filter',
        'hierarchy_drill_down',
        'fusion',
    ]
    assert result.rerank_complete.top5
    assert [stage.name for stage in result.rerank_complete.cascade_trace] == ['rerank', 'final_evidence']
    assert result.retrieval_complete.iterative_trace is not None
    assert result.retrieval_complete.iterative_trace.enabled is True
    assert 2 <= len(result.retrieval_complete.iterative_trace.steps) <= 3
    assert result.retrieval_complete.iterative_trace.steps[0].selected_evidence_ids
    assert result.rerank_complete.cascade_trace[-1].metadata['compressed_count'] == len(result.done.citations)
    assert result.rerank_complete.top5[0].citation_id == 1
    assert result.done.latency_ms >= 1
    assert result.done.total_tokens >= 1


def test_workflow_passes_retrieval_plan_to_retriever():
    class RecordingRetriever:
        def __init__(self):
            self.received_plan = None

        def retrieve(self, query, top_k=None, plan=None):
            self.received_plan = plan
            item = RetrievalResultItem(
                chunk_id="chunk-1",
                title="CATL risk note",
                doc_type="research_report",
                company="宁德时代",
                date="2026-01-01",
                page=1,
                preview="经营风险",
                score=1.0,
                content="经营风险",
                metadata={},
            )
            return HybridRetrievalResult(
                bm25_results=[item],
                vector_results=[item],
                fused_top20=[item],
            )

    retriever = RecordingRetriever()
    workflow = QueryWorkflow(retriever=retriever, rerank_service=RerankService())
    workflow.run(QueryRequest(query="宁德时代近期有哪些潜在经营风险？"))

    assert retriever.received_plan is not None
    assert retriever.received_plan.retrieval_strategy == "research_report_analysis"


def test_workflow_keeps_metric_lookup_single_pass():
    class CountingRetriever:
        def __init__(self):
            self.calls = []

        def retrieve(self, query, top_k=None, plan=None):
            self.calls.append(query)
            item = RetrievalResultItem(
                chunk_id="fact-1",
                title="NVIDIA revenue",
                doc_type="financial_report",
                company="NVIDIA",
                date="2025-11-19",
                page=1,
                preview="Revenue = 57,006",
                score=1.0,
                content="Revenue = 57,006",
                metadata={"chunk_type": "table_fact", "metric": "revenue", "raw_value": "57,006"},
            )
            return HybridRetrievalResult(bm25_results=[item], vector_results=[item], fused_top20=[item])

    retriever = CountingRetriever()
    workflow = QueryWorkflow(retriever=retriever, rerank_service=RerankService())
    result = workflow.run(QueryRequest(query="英伟达2026年第三季度的总营收是多少？"))

    assert len(retriever.calls) == 1
    assert result.retrieval_complete.iterative_trace is None


def test_workflow_iterative_step_failure_falls_back_to_single_pass():
    class FailingStepRetriever:
        def __init__(self):
            self.calls = 0

        def retrieve(self, query, top_k=None, plan=None):
            self.calls += 1
            if self.calls > 1:
                raise RuntimeError("step failed")
            item = RetrievalResultItem(
                chunk_id="chunk-1",
                title="CATL risk note",
                doc_type="research_report",
                company="宁德时代",
                date="2026-01-01",
                page=1,
                preview="经营风险",
                score=1.0,
                content="经营风险",
                metadata={},
            )
            return HybridRetrievalResult(bm25_results=[item], vector_results=[item], fused_top20=[item])

    workflow = QueryWorkflow(retriever=FailingStepRetriever(), rerank_service=RerankService())
    result = workflow.run(QueryRequest(query="宁德时代近期有哪些潜在经营风险？"))

    assert result.degraded is True
    assert result.fallback_reason == "iterative_step_failed"
    assert result.retrieval_complete.iterative_trace is not None
    assert result.retrieval_complete.iterative_trace.degraded is True
    assert result.rerank_complete.top5


def test_workflow_iterative_planning_failure_falls_back_to_single_pass(monkeypatch):
    def fail_planning(query, plan):
        raise RuntimeError("planning failed")

    monkeypatch.setattr("app.core.agent.workflow.plan_iterative_retrieval", fail_planning)
    workflow = _workflow()
    result = workflow.run(QueryRequest(query="宁德时代近期有哪些潜在经营风险？"))

    assert result.degraded is True
    assert result.fallback_reason == "iterative_planning_failed"
    assert result.retrieval_complete.iterative_trace is not None
    assert result.retrieval_complete.iterative_trace.degraded is True
    assert result.rerank_complete.top5


def test_workflow_iterative_no_evidence_falls_back_to_single_pass():
    class EmptyAfterSinglePassRetriever:
        def __init__(self):
            self.calls = 0

        def retrieve(self, query, top_k=None, plan=None):
            self.calls += 1
            item = RetrievalResultItem(
                chunk_id="chunk-1",
                title="CATL risk note",
                doc_type="research_report",
                company="宁德时代",
                date="2026-01-01",
                page=1,
                preview="经营风险",
                score=1.0,
                content="经营风险",
                metadata={},
            )
            if self.calls == 1:
                return HybridRetrievalResult(bm25_results=[item], vector_results=[item], fused_top20=[item])
            return HybridRetrievalResult(bm25_results=[], vector_results=[], fused_top20=[])

    workflow = QueryWorkflow(retriever=EmptyAfterSinglePassRetriever(), rerank_service=RerankService())
    result = workflow.run(QueryRequest(query="宁德时代近期有哪些潜在经营风险？"))

    assert result.degraded is True
    assert result.fallback_reason == "iterative_no_evidence"
    assert result.retrieval_complete.iterative_trace is not None
    assert result.retrieval_complete.iterative_trace.degraded is True
    assert result.rerank_complete.top5


def test_mock_answer_falls_back_when_no_evidence():
    _, intent = analyze_query('未知公司收入是多少？')

    assert build_mock_answer('未知公司收入是多少？', intent, []) == '资料中未提及。'
