from app.core.agent.query_analysis import analyze_query, classify_intent


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
