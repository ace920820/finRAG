from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.schemas import RetrievalPlan, RetrievalStrategy


@dataclass(frozen=True)
class RouteDecision:
    route: RetrievalStrategy
    reason: str


def choose_route(plan: Optional[RetrievalPlan], query: str) -> RouteDecision:
    if plan is None:
        return RouteDecision(route="general_hybrid", reason="no_plan")

    if plan.task_type == "metric_lookup" and plan.entities and plan.metrics:
        return RouteDecision(route="table_fact_first", reason="entity_metric_lookup")

    if plan.task_type in {"risk_analysis", "causal_analysis", "trend_analysis", "comparison"}:
        return RouteDecision(route="research_report_analysis", reason=f"task:{plan.task_type}")

    if plan.entities and plan.time_range and plan.time_range.year is not None and not plan.metrics:
        return RouteDecision(route="financial_report_first", reason="entity_time_filing_lookup")

    if plan.retrieval_strategy in {"table_fact_first", "financial_report_first", "research_report_analysis"}:
        return RouteDecision(route=plan.retrieval_strategy, reason="plan_strategy")

    return RouteDecision(route="general_hybrid", reason="fallback")
