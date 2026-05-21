from app.core.agent.query_analysis import analyze_query, classify_intent


def test_query_plan_extracts_nvidia_metric_lookup():
    rewrite, intent = analyze_query('英伟达2026年第三季度的总营收是多少？')

    assert rewrite.plan.original_query == '英伟达2026年第三季度的总营收是多少？'
    assert rewrite.plan.entities[0].canonical == 'NVIDIA'
    assert rewrite.plan.metrics[0].canonical == 'revenue'
    assert rewrite.plan.time_range.year == 2026
    assert rewrite.plan.time_range.quarter == 'q3'
    assert rewrite.plan.task_type == 'metric_lookup'
    assert rewrite.plan.retrieval_strategy == 'table_fact_first'
    assert intent.intent == 'factual'


def test_query_plan_extracts_moutai_causal_recent_years():
    rewrite, intent = analyze_query('贵州茅台近年净利润变化原因')

    assert rewrite.plan.entities[0].canonical == '贵州茅台'
    assert rewrite.plan.metrics[0].canonical == 'net_income'
    assert rewrite.plan.time_range.relative == 'recent_years'
    assert rewrite.plan.task_type == 'causal_analysis'
    assert rewrite.plan.retrieval_strategy == 'research_report_analysis'
    assert intent.intent in {'analytical', 'reasoning'}


def test_query_plan_extracts_catl_risk_recent():
    rewrite, intent = analyze_query('宁德时代近期有哪些潜在经营风险？')

    assert rewrite.plan.entities[0].canonical == '宁德时代'
    assert rewrite.plan.time_range.relative == 'recent'
    assert rewrite.plan.task_type == 'risk_analysis'
    assert rewrite.plan.retrieval_strategy == 'research_report_analysis'
    assert intent.intent == 'analytical'


def test_query_plan_extracts_reasoning_macro_industry_question():
    rewrite, intent = analyze_query('宏观消费变化如何影响白酒行业？')

    assert intent.intent == 'reasoning'
    assert rewrite.plan.intent == 'reasoning'
    assert rewrite.plan.task_type == 'causal_analysis'
    assert rewrite.plan.retrieval_strategy == 'research_report_analysis'
    assert 'research_report' in rewrite.plan.preferred_doc_types
    assert rewrite.plan.signals
    assert any(signal.startswith('task:') or signal.startswith('strategy:') for signal in rewrite.plan.signals)


def test_query_plan_extracts_tsmc_financial_period():
    rewrite, _ = analyze_query('TSMC 2026Q3 revenue')

    assert rewrite.plan.entities[0].canonical == '台积电'
    assert rewrite.plan.metrics[0].canonical == 'revenue'
    assert rewrite.plan.time_range.year == 2026
    assert rewrite.plan.time_range.quarter == 'q3'
    assert 'financial_report' in rewrite.plan.preferred_doc_types


def test_query_plan_uses_dateparser_fallback_for_ordinary_date():
    rewrite, _ = analyze_query('英伟达 November 19 2025 revenue')

    assert rewrite.plan.time_range.year == 2025
    assert 'November 19 2025' in rewrite.plan.time_range.raw
    assert 'time_fallback:dateparser' in rewrite.plan.signals


def test_query_rewrite_expands_moutai_aliases():
    rewrite, intent = analyze_query('贵州茅台 2023 年营业收入是多少？同比增长率？')

    assert rewrite.original.startswith('贵州茅台')
    assert '茅台' in rewrite.expanded
    assert '营业收入' in rewrite.expanded
    assert intent.intent == 'factual'


def test_query_rewrite_expands_catl_risk_terms():
    rewrite, intent = analyze_query('宁德时代近期有哪些潜在经营风险？')

    assert 'CATL' in rewrite.expanded
    assert '经营风险' in rewrite.expanded
    assert rewrite.sub_queries
    assert intent.intent == 'analytical'


def test_query_rewrite_expands_nvidia_aliases():
    rewrite, intent = analyze_query('英伟达最近营收的信息是？')

    assert 'NVIDIA' in rewrite.expanded
    assert 'NVDA' in rewrite.expanded
    assert 'revenue' in rewrite.expanded
    assert intent.intent == 'factual'


def test_reasoning_intent_for_macro_industry_question():
    assert classify_intent('宏观消费变化如何影响白酒行业？') == 'reasoning'
