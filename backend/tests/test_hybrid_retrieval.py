from app.core.ingestion.fixture_loader import load_chunks
from app.core.agent.query_analysis import analyze_query
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.bm25_store import BM25Result, BM25Store
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.core.retrieval.vector_store import VectorStore
from app.models.schemas import Chunk, QueryEntity, RetrievalPlan


class EmptyVectorStore(VectorStore):
    def __init__(self):
        pass

    def search(self, query: str, top_k: int = 20, embedding_provider=None):
        return []


class EmptyBM25Store:
    chunks = []

    def search(self, query: str, top_k: int = 20):
        return []


def _plan(strategy='research_report_analysis', company='宁德时代', aliases=None):
    return RetrievalPlan(
        original_query=f'{company}经营风险',
        normalized_query=f'{company}经营风险',
        intent='analytical',
        task_type='risk_analysis',
        entities=[QueryEntity(canonical=company, aliases=aliases or [], match=company)],
        preferred_doc_types=['financial_report'] if strategy == 'financial_report_first' else ['research_report'],
        retrieval_strategy=strategy,
    )


def test_hybrid_retrieval_returns_separate_stage_outputs():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    result = retriever.retrieve('宁德时代 经营风险', top_k=20)

    assert result.bm25_results
    assert result.vector_results
    assert result.fused_top20
    first = result.fused_top20[0]
    assert first.chunk_id
    assert first.title
    assert first.preview


def test_rrf_fusion_is_deterministic():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    first = retriever.retrieve('贵州茅台 营业收入', top_k=20).fused_top20
    second = retriever.retrieve('贵州茅台 营业收入', top_k=20).fused_top20
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]


def test_query_plan_routes_table_fact_first_for_nvidia_revenue():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    rewrite, _ = analyze_query('英伟达2026年第三季度的总营收是多少？')
    result = retriever.retrieve(rewrite.original, top_k=20, plan=rewrite.plan)

    assert result.route == 'table_fact_first'
    assert result.route_reason
    assert result.fused_top20
    assert any(item.metadata.get('chunk_type') == 'table_fact' for item in result.fused_top20)
    stage_names = [stage.name for stage in result.cascade_trace]
    assert stage_names[:4] == ['query_plan', 'coarse_recall', 'metadata_filter', 'fusion']
    assert all(stage.method and stage.input_count is not None and stage.output_count is not None for stage in result.cascade_trace)


def test_query_plan_routes_research_report_analysis_for_catl_risk():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    rewrite, _ = analyze_query('宁德时代近期有哪些潜在经营风险？')
    result = retriever.retrieve(rewrite.original, top_k=20, plan=rewrite.plan)

    assert result.route == 'research_report_analysis'
    assert result.route_reason
    assert result.fused_top20


def test_query_plan_routes_financial_report_first_for_company_filing_lookup():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    rewrite, _ = analyze_query('台积电2026Q3财报营收')
    result = retriever.retrieve(rewrite.original, top_k=20, plan=rewrite.plan)

    assert result.route == 'financial_report_first'
    assert result.route_reason
    assert result.fused_top20


def test_hierarchy_drill_down_expands_recalled_section_parent():
    section_parent = Chunk(
        chunk_id='doc-catl-s0000-risk',
        doc_id='doc-catl',
        section='经营风险',
        chunk_index=0,
        content='Section: 经营风险\n\n原材料价格波动影响盈利能力。',
        metadata={
            'chunk_type': 'section',
            'chunk_level': 'section',
            'child_ids': ['doc-catl-c0000-risk'],
            'company': '宁德时代',
            'doc_type': 'research_report',
            'date': '2026-05-01',
            'source': 'CATL report',
        },
    )
    child = Chunk(
        chunk_id='doc-catl-c0000-risk',
        doc_id='doc-catl',
        section='chunk-1',
        chunk_index=1,
        content='供应合同条款、上游价格机制和客户需求变化。',
        metadata={
            'chunk_type': 'text',
            'chunk_level': 'paragraph',
            'parent_id': section_parent.chunk_id,
            'company': '宁德时代',
            'doc_type': 'research_report',
            'date': '2026-05-01',
            'source': 'CATL report',
        },
    )
    retriever = HybridRetriever(BM25Store.from_chunks([section_parent, child]), EmptyVectorStore())

    result = retriever.retrieve('宁德时代经营风险', top_k=1, plan=_plan())

    stage = next(item for item in result.cascade_trace if item.name == 'hierarchy_drill_down')
    assert stage.input_count >= 1
    assert stage.output_count == 1
    assert stage.metadata['children_per_parent_limit'] == 3
    assert any(item.chunk_id == child.chunk_id for item in result.fused_top20)


def test_hierarchy_drill_down_expands_table_parent_and_dedupes_existing_child():
    table_parent = Chunk(
        chunk_id='doc-nvda-t0000-income',
        doc_id='doc-nvda',
        section='table:income',
        chunk_index=0,
        content='Table: income\nRevenue rows',
        metadata={
            'chunk_type': 'table',
            'chunk_level': 'table',
            'child_ids': ['doc-nvda-tr0000-margin'],
            'company': 'NVIDIA',
            'doc_type': 'financial_report',
            'date': '2025-11-19',
            'source': 'NVDA 10Q',
        },
    )
    margin_child = Chunk(
        chunk_id='doc-nvda-tr0000-margin',
        doc_id='doc-nvda',
        section='table:income:row:0',
        chunk_index=1,
        content='Table Row Metric: gross_margin\nGross margin improved.',
        metadata={
            'chunk_type': 'table_row',
            'chunk_level': 'table_row',
            'parent_id': table_parent.chunk_id,
            'metric': 'gross_margin',
            'company': 'NVIDIA',
            'doc_type': 'financial_report',
            'date': '2025-11-19',
            'source': 'NVDA 10Q',
        },
    )
    retriever = HybridRetriever(BM25Store.from_chunks([table_parent, margin_child]), EmptyVectorStore())

    result = retriever.retrieve('NVIDIA financial report overview', top_k=1, plan=_plan(strategy='financial_report_first', company='NVIDIA', aliases=['NVDA']))

    stage = next(item for item in result.cascade_trace if item.name == 'hierarchy_drill_down')
    result_ids = [item.chunk_id for item in result.fused_top20]
    assert stage.output_count <= 1
    assert result_ids.count(margin_child.chunk_id) == 1


def test_metadata_filters_relax_when_too_narrow(monkeypatch):
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    rewrite, _ = analyze_query('英伟达 November 19 2025 revenue')
    rewrite.plan.filters['collection'] = 'nonexistent'
    result = retriever.retrieve(rewrite.original, top_k=20, plan=rewrite.plan)

    assert result.filters_relaxed is True
    assert result.filter_fallback_reason
    assert result.filter_before_count is not None
    assert result.filter_after_count is not None
    metadata_filter = next(stage for stage in result.cascade_trace if stage.name == 'metadata_filter')
    assert metadata_filter.degraded is True
    assert metadata_filter.fallback_reason
    assert metadata_filter.metadata['applied_at'] == 'post_recall'


def test_string_only_retrieval_returns_cascade_trace():
    retriever = HybridRetriever.from_chunks(load_chunks(), MockEmbeddingProvider())
    result = retriever.retrieve('宁德时代 经营风险', top_k=20)

    stage_names = [stage.name for stage in result.cascade_trace]
    assert stage_names == ['query_plan', 'coarse_recall', 'metadata_filter', 'fusion']
    coarse_recall = next(stage for stage in result.cascade_trace if stage.name == 'coarse_recall')
    assert coarse_recall.metadata['bm25_count'] >= 0
    assert coarse_recall.metadata['vector_count'] >= 0


def test_nvidia_fy2026_q3_revenue_query_retrieves_income_statement(monkeypatch):
    table_fact = {
        'fact_id': 'fact-nvda-q3-revenue',
        'company': 'NVIDIA',
        'metric': 'revenue',
        'metric_label': 'Revenue',
        'period_label': 'FY2026 Q3 three months ended',
        'raw_value': '57,006',
        'value': 57006,
        'unit': 'USD millions',
        'currency': 'USD',
        'source_pdf_name': 'NVDA_nvidia_10q_FY2026Q3_2025-11-19.pdf',
        'table_id': 'tbl-income',
        'row_index': 0,
        'column_index': 1,
    }
    monkeypatch.setattr('app.core.retrieval.table_facts.load_table_facts', lambda: [table_fact])

    retrieval = HybridRetriever(EmptyBM25Store(), EmptyVectorStore()).retrieve('英伟达2026年第三季度的总营收是多少？')
    rerank = RerankService().rerank('英伟达2026年第三季度的总营收是多少？', retrieval.fused_top20)

    top_text = ' '.join(item.content for item in rerank.top5[:3])
    assert 'NVDA_nvidia_10q_FY2026Q3' in rerank.top5[0].title
    assert 'Revenue' in top_text and '57,006' in top_text
    assert any(item.metadata.get('chunk_type') == 'table_fact' for item in rerank.top5)
    table_fact_hit = next(item for item in rerank.top5 if item.metadata.get('chunk_type') == 'table_fact')
    assert table_fact_hit.metadata['metric'] == 'revenue'
    assert table_fact_hit.metadata['raw_value'] == '57,006'
    assert any(item.metadata.get('chunk_type') in {'table_fact', 'table'} for item in rerank.top5)


def test_hybrid_fusion_suppresses_table_fact_when_requested_year_mismatches():
    retriever = HybridRetriever(EmptyBM25Store(), EmptyVectorStore())
    table_fact = BM25Result(
        chunk_id='fact-2026',
        score=12.0,
        title='NVDA FY2026Q3',
        doc_type='financial_report',
        company='NVIDIA',
        date='2025-11-19',
        page=None,
        preview='Table fact: Revenue = 57,006 | period: FY2026 Q3',
        content='Table fact: Revenue = 57,006 | period: FY2026 Q3',
        metadata={
            'chunk_type': 'table_fact',
            'metric': 'revenue',
            'period_label': 'FY2026 Q3',
            'source': 'NVDA_nvidia_10q_FY2026Q3_2025-11-19.pdf',
            'fact_reasons': ['company', 'metric', 'source_year:2026'],
        },
    )

    fused = retriever._rrf_fuse('英伟达2024年第三季度的总营收是多少？', [], [], [table_fact], top_k=5)

    assert fused == []
