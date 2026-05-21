from app.core.agent.query_analysis import analyze_query
from app.core.agent.retrieval_planner import MAX_ITERATIVE_STEPS, plan_iterative_retrieval, should_use_iterative_retrieval


def _plan(query: str):
    rewrite, _ = analyze_query(query)
    return rewrite.plan


def test_catl_risk_query_is_iterative_and_purposeful():
    plan = _plan("宁德时代近期有哪些潜在经营风险？")
    trace = plan_iterative_retrieval("宁德时代近期有哪些潜在经营风险？", plan)

    assert should_use_iterative_retrieval(plan) is True
    assert trace.enabled is True
    assert 2 <= len(trace.steps) <= 3
    assert [step.purpose for step in trace.steps][:2] == ["background_facts", "risk_or_driver_evidence"]
    assert "宁德时代" in trace.steps[0].retrieval_query
    assert "风险" in trace.steps[1].retrieval_query


def test_causal_query_has_deterministic_cross_check_step():
    plan = _plan("宏观消费变化如何影响贵州茅台盈利能力？")
    first = plan_iterative_retrieval("宏观消费变化如何影响贵州茅台盈利能力？", plan)
    second = plan_iterative_retrieval("宏观消费变化如何影响贵州茅台盈利能力？", plan)

    assert [step.purpose for step in first.steps] == [step.purpose for step in second.steps]
    assert [step.retrieval_query for step in first.steps] == [step.retrieval_query for step in second.steps]
    assert first.steps[-1].purpose == "cross_check"


def test_comparison_query_can_include_cross_check():
    plan = _plan("台积电和英伟达的收入趋势对比？")
    trace = plan_iterative_retrieval("台积电和英伟达的收入趋势对比？", plan)

    assert trace.enabled is True
    assert trace.steps[-1].purpose == "cross_check"


def test_nvidia_revenue_lookup_is_not_iterative():
    plan = _plan("英伟达2026年第三季度的总营收是多少？")
    trace = plan_iterative_retrieval("英伟达2026年第三季度的总营收是多少？", plan)

    assert should_use_iterative_retrieval(plan) is False
    assert trace.enabled is False
    assert trace.steps == []


def test_iterative_planner_never_exceeds_max_steps():
    plan = _plan("宁德时代近期有哪些潜在经营风险？")
    trace = plan_iterative_retrieval("宁德时代近期有哪些潜在经营风险？", plan)

    assert len(trace.steps) <= MAX_ITERATIVE_STEPS
