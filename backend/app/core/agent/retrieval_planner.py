from __future__ import annotations

from app.models.schemas import IterativeRetrievalStep, IterativeRetrievalTrace, RetrievalPlan


ITERATIVE_TASK_TYPES = {"risk_analysis", "causal_analysis", "trend_analysis", "comparison"}
MAX_ITERATIVE_STEPS = 3


def should_use_iterative_retrieval(plan: RetrievalPlan | None) -> bool:
    if plan is None:
        return False
    if plan.retrieval_strategy == "table_fact_first":
        return False
    return plan.task_type in ITERATIVE_TASK_TYPES


def plan_iterative_retrieval(query: str, plan: RetrievalPlan | None) -> IterativeRetrievalTrace:
    if not should_use_iterative_retrieval(plan):
        return IterativeRetrievalTrace(enabled=False, fallback_reason="iterative_not_applicable")
    assert plan is not None
    anchors = _anchors(plan)
    steps = [
        IterativeRetrievalStep(
            index=1,
            purpose="background_facts",
            retrieval_query=_join_query(query, anchors, "相关事实依据"),
        ),
        IterativeRetrievalStep(
            index=2,
            purpose="risk_or_driver_evidence",
            retrieval_query=_driver_query(query, plan, anchors),
        ),
    ]
    if plan.task_type in {"comparison", "causal_analysis", "risk_analysis"}:
        steps.append(
            IterativeRetrievalStep(
                index=3,
                purpose="cross_check",
                retrieval_query=_join_query(query, anchors, "交叉验证 对比 反向证据"),
            )
        )
    return IterativeRetrievalTrace(enabled=True, steps=steps[:MAX_ITERATIVE_STEPS])


def _anchors(plan: RetrievalPlan) -> str:
    parts: list[str] = []
    parts.extend(entity.canonical for entity in plan.entities)
    parts.extend(metric.canonical for metric in plan.metrics)
    if plan.time_range and plan.time_range.raw:
        parts.append(plan.time_range.raw)
    return " ".join(_unique(parts))


def _driver_query(query: str, plan: RetrievalPlan, anchors: str) -> str:
    if plan.task_type == "risk_analysis":
        suffix = "经营风险 政策变化 竞争 原材料 盈利能力"
    elif plan.task_type == "trend_analysis":
        suffix = "趋势变化 驱动因素 财务表现"
    elif plan.task_type == "comparison":
        suffix = "对比差异 关键指标 竞争格局"
    else:
        suffix = "原因 影响 传导机制 驱动因素"
    return _join_query(query, anchors, suffix)


def _join_query(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
