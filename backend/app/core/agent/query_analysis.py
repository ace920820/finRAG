from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from app.core.agent.query_ontology import QUARTER_ALIASES, match_companies, match_metrics, normalize_query
from app.models.events import IntentDetectedEvent, QueryRewriteEvent
from app.models.schemas import QueryEntity, QueryIntent, QueryMetric, QueryTaskType, QueryTimeRange, RetrievalPlan, RetrievalStrategy


_REASONING_HINTS = ("对比", "比较", "传导", "影响", "宏观", "行业", "为什么", "如何")
_ANALYTICAL_HINTS = ("风险", "分析", "潜在", "趋势", "逻辑", "判断", "原因", "机会")
_FACTUAL_HINTS = ("多少", "是多少", "同比", "增长率", "收入", "营收", "净利润", "数据")


def analyze_query(query: str) -> tuple[QueryRewriteEvent, IntentDetectedEvent]:
    original = query.strip()
    normalized = normalize_query(original)
    intent = classify_intent(original)
    plan = build_retrieval_plan(original, normalized, intent)
    expanded = _expand_terms(original, plan)
    rewrite = QueryRewriteEvent(
        original=original,
        expanded=expanded,
        sub_queries=_build_sub_queries(original, intent, expanded),
        plan=plan,
    )
    return rewrite, IntentDetectedEvent(intent=intent, template=_template_for_intent(intent))


def classify_intent(query: str) -> QueryIntent:
    if any(hint in query for hint in _REASONING_HINTS):
        return "reasoning"
    if any(hint in query for hint in _ANALYTICAL_HINTS):
        return "analytical"
    if any(hint in query for hint in _FACTUAL_HINTS):
        return "factual"
    return "analytical"


def build_retrieval_plan(original_query: str, normalized_query: str, intent: QueryIntent) -> RetrievalPlan:
    company_matches = match_companies(normalized_query)
    metric_matches = match_metrics(normalized_query)
    time_range, time_signals = _parse_time_range(original_query, normalized_query)
    task_type = _infer_task_type(original_query, normalized_query, intent, metric_matches)
    retrieval_strategy = _infer_retrieval_strategy(original_query, task_type, company_matches, metric_matches, time_range)
    preferred_doc_types = _preferred_doc_types(task_type, retrieval_strategy)
    filters = _build_filters(company_matches, metric_matches, time_range)
    signals = _build_signals(task_type, retrieval_strategy, company_matches, metric_matches, time_signals)
    return RetrievalPlan(
        original_query=original_query,
        normalized_query=normalized_query,
        intent=intent,
        task_type=task_type,
        entities=[QueryEntity(**match) for match in company_matches],
        metrics=[QueryMetric(**match) for match in metric_matches],
        time_range=time_range,
        preferred_doc_types=preferred_doc_types,
        retrieval_strategy=retrieval_strategy,
        filters=filters,
        signals=signals,
    )


def detect_entities(query: str) -> List[str]:
    normalized = normalize_query(query)
    return [match["canonical"] for match in match_companies(normalized)]


def _expand_terms(query: str, plan: RetrievalPlan) -> List[str]:
    terms: List[str] = []
    for entity in plan.entities:
        terms.extend(_entity_expansions(entity.canonical, entity.aliases))
    for metric in plan.metrics:
        terms.extend([metric.canonical] + metric.aliases[:2])
    if "风险" in query:
        terms.extend(["经营风险", "政策变化", "原材料价格", "盈利能力"])
    if "收入" in query or "营收" in query or "营业收入" in query:
        terms.extend(["营业收入", "同比增长", "主要会计数据", "revenue", "net revenue"])
    if "宏观" in query or "行业" in query:
        terms.extend(["宏观消费", "行业竞争", "供应链", "需求变化"])
    return _unique(terms)


def _entity_expansions(canonical: str, aliases: list[str]) -> list[str]:
    if canonical == "NVIDIA":
        return ["NVIDIA", "NVDA", "nvidia", "英伟达"]
    if canonical == "贵州茅台":
        return ["贵州茅台", "茅台", "600519", "moutai"]
    if canonical == "宁德时代":
        return ["宁德时代", "CATL", "catl", "300750"]
    if canonical == "台积电":
        return ["台积电", "TSMC", "tsmc", "2330"]
    return [canonical] + aliases[:2]


def _build_sub_queries(query: str, intent: QueryIntent, expanded: List[str]) -> List[str]:
    if intent == "factual":
        return [query]
    if intent == "reasoning":
        anchors = " ".join(expanded[:4]) if expanded else query
        return [
            f"{query} 相关事实依据",
            f"{anchors} 对公司经营和行业变量的影响",
        ]
    return [query, f"{query} 相关风险因素与证据"]


def _template_for_intent(intent: QueryIntent) -> str:
    templates = {
        "factual": "factual_markdown_with_citations",
        "analytical": "analytical_markdown_with_citations",
        "reasoning": "reasoning_markdown_with_citations",
    }
    return templates[intent]


def _infer_task_type(
    original_query: str,
    normalized_query: str,
    intent: QueryIntent,
    metric_matches: list[dict[str, object]],
) -> QueryTaskType:
    if any(token in original_query for token in ("风险", "潜在")):
        return "risk_analysis"
    if any(token in original_query for token in ("原因", "为什么", "如何", "影响")) or intent == "reasoning":
        return "causal_analysis"
    if any(token in normalized_query for token in ("对比", "比较")):
        return "comparison"
    if metric_matches and any(token in original_query for token in ("多少", "是多少", "营收", "收入", "净利润")):
        return "metric_lookup"
    if metric_matches and any(token in normalized_query for token in ("revenue", "income", "eps", "profit")):
        return "metric_lookup"
    if metric_matches and re.search(r"20\d{2}\s*q?[1-4]", normalized_query):
        return "metric_lookup"
    if metric_matches and any(token in original_query for token in ("财报", "报表", "财务", "业绩")):
        return "metric_lookup"
    if any(token in original_query for token in ("趋势", "变化")):
        return "trend_analysis"
    return "general_analysis"


def _infer_retrieval_strategy(
    original_query: str,
    task_type: QueryTaskType,
    companies: list[dict[str, object]],
    metrics: list[dict[str, object]],
    time_range: Optional[QueryTimeRange],
) -> RetrievalStrategy:
    if companies and time_range and time_range.year and any(token in original_query for token in ("财报", "报表", "年报", "季报", "10k", "10q")):
        if not any(token in original_query for token in ("多少", "是多少", "具体", "几", "金额", "值")):
            return "financial_report_first"
    if task_type == "metric_lookup" and companies and metrics:
        return "table_fact_first"
    if task_type in {"risk_analysis", "causal_analysis", "trend_analysis", "comparison"}:
        return "research_report_analysis"
    if companies and time_range and time_range.year and not metrics:
        return "financial_report_first"
    return "general_hybrid"


def _preferred_doc_types(task_type: QueryTaskType, retrieval_strategy: RetrievalStrategy) -> list[str]:
    if retrieval_strategy == "table_fact_first":
        return ["financial_report"]
    if retrieval_strategy == "financial_report_first":
        return ["financial_report", "research_report"]
    if retrieval_strategy == "research_report_analysis":
        return ["research_report", "financial_report"]
    if task_type == "general_analysis":
        return ["research_report", "financial_report", "news"]
    return ["research_report", "financial_report"]


def _build_filters(
    companies: list[dict[str, object]],
    metrics: list[dict[str, object]],
    time_range: Optional[QueryTimeRange],
) -> dict[str, object]:
    filters: dict[str, object] = {}
    if companies:
        filters["company"] = [item["canonical"] for item in companies]
    if metrics:
        filters["metric"] = [item["canonical"] for item in metrics]
    if time_range and time_range.year is not None:
        filters["year"] = time_range.year
    if time_range and time_range.quarter:
        filters["quarter"] = time_range.quarter
    return filters


def _build_signals(
    task_type: QueryTaskType,
    retrieval_strategy: RetrievalStrategy,
    companies: list[dict[str, object]],
    metrics: list[dict[str, object]],
    time_signals: list[str],
) -> list[str]:
    signals = [f"task:{task_type}", f"strategy:{retrieval_strategy}"]
    if companies:
        signals.append("entity:matched")
    if metrics:
        signals.append("metric:matched")
    signals.extend(time_signals)
    return _unique(signals)


def _parse_time_range(original_query: str, normalized_query: str) -> tuple[Optional[QueryTimeRange], list[str]]:
    year = _extract_year(normalized_query)
    quarter = _extract_quarter(normalized_query)
    fiscal = bool(re.search(r"\b(?:fy|fiscal|财报)\b", normalized_query))
    if any(token in original_query for token in ("最新", "最近", "近期")):
        return QueryTimeRange(year=year, quarter=quarter, fiscal=fiscal, relative="recent", raw=original_query), ["time:recent"]
    if any(token in original_query for token in ("近年", "近年来")):
        return QueryTimeRange(year=year, quarter=quarter, fiscal=fiscal, relative="recent_years", raw=original_query), ["time:recent_years"]
    ordinary_date = _match_ordinary_date(original_query)
    if ordinary_date:
        parsed = _parse_ordinary_date(ordinary_date.group(0))
        signals = ["time_fallback:dateparser"]
        return QueryTimeRange(year=parsed.year if parsed else year, quarter=quarter, fiscal=fiscal, raw=ordinary_date.group(0)), signals
    if year or quarter:
        return QueryTimeRange(year=year, quarter=quarter, fiscal=fiscal, raw=original_query), _time_signals(year, quarter, fiscal)
    fallback = _dateparser_fallback(original_query)
    if fallback:
        return fallback
    return None, []


def _dateparser_fallback(original_query: str) -> tuple[QueryTimeRange, list[str]]:
    match = _match_ordinary_date(original_query)
    if not match:
        return QueryTimeRange(raw=None), []
    text = match.group(0)
    parsed = _parse_ordinary_date(text)
    if parsed is None:
        return QueryTimeRange(raw=text), ["time_fallback:dateparser"]
    return QueryTimeRange(year=parsed.year, raw=text), ["time_fallback:dateparser"]


def _parse_ordinary_date(text: str) -> Optional[datetime]:
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(text, "%B %d %Y")
    except ValueError:
        return None


def _match_ordinary_date(original_query: str):
    return re.search(r"(20\d{2}\s+[A-Za-z]+\s+\d{1,2}|[A-Za-z]+\s+\d{1,2}\s+20\d{2}|20\d{2}-\d{2}-\d{2})", original_query)


def _extract_year(normalized_query: str) -> Optional[int]:
    match = re.search(r"(20\d{2})", normalized_query)
    return int(match.group(1)) if match else None


def _extract_quarter(normalized_query: str) -> Optional[str]:
    for quarter, aliases in QUARTER_ALIASES.items():
        if any(alias.lower() in normalized_query for alias in aliases):
            return quarter
    match = re.search(r"20\d{2}\s*q([1-4])", normalized_query)
    if match:
        return f"q{match.group(1)}"
    return None


def _time_signals(year: Optional[int], quarter: Optional[str], fiscal: bool) -> list[str]:
    signals: list[str] = []
    if year is not None:
        signals.append(f"time:year:{year}")
    if quarter is not None:
        signals.append(f"time:quarter:{quarter}")
    if fiscal:
        signals.append("time:fiscal")
    return signals


def _unique(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
