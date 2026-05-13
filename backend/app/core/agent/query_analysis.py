from __future__ import annotations

from typing import List

from app.models.events import IntentDetectedEvent, QueryRewriteEvent
from app.models.schemas import QueryIntent


_COMPANY_ALIASES = {
    "贵州茅台": ["贵州茅台", "茅台", "600519", "白酒", "营业收入", "同比增长"],
    "茅台": ["贵州茅台", "茅台", "600519", "白酒"],
    "宁德时代": ["宁德时代", "CATL", "300750", "动力电池", "新能源车", "经营风险"],
    "CATL": ["宁德时代", "CATL", "300750", "动力电池"],
    "英伟达": ["英伟达", "NVIDIA", "NVDA", "revenue", "net revenue", "Data Center"],
    "NVIDIA": ["英伟达", "NVIDIA", "NVDA", "revenue", "net revenue", "Data Center"],
    "NVDA": ["英伟达", "NVIDIA", "NVDA", "revenue", "net revenue", "Data Center"],
}

_REASONING_HINTS = ("对比", "比较", "传导", "影响", "宏观", "行业", "为什么", "如何")
_ANALYTICAL_HINTS = ("风险", "分析", "潜在", "趋势", "逻辑", "判断", "原因", "机会")
_FACTUAL_HINTS = ("多少", "是多少", "同比", "增长率", "收入", "营收", "净利润", "数据")


def analyze_query(query: str) -> tuple[QueryRewriteEvent, IntentDetectedEvent]:
    normalized_query = query.strip()
    expanded = _expand_terms(normalized_query)
    intent = classify_intent(normalized_query)
    rewrite = QueryRewriteEvent(
        original=normalized_query,
        expanded=expanded,
        sub_queries=_build_sub_queries(normalized_query, intent, expanded),
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


def detect_entities(query: str) -> List[str]:
    entities: List[str] = []
    if "贵州茅台" in query or "茅台" in query or "600519" in query:
        entities.append("贵州茅台")
    if "宁德时代" in query or "CATL" in query or "300750" in query:
        entities.append("宁德时代")
    if "英伟达" in query or "NVIDIA" in query or "NVDA" in query:
        entities.append("英伟达")
    if "美联储" in query or "加息" in query:
        entities.append("美联储")
    if "新能源" in query or "动力电池" in query:
        entities.append("新能源板块")
    return _unique(entities)


def _expand_terms(query: str) -> List[str]:
    terms: List[str] = []
    for alias, expansions in _COMPANY_ALIASES.items():
        if alias in query:
            terms.extend(expansions)
    if "风险" in query:
        terms.extend(["经营风险", "政策变化", "原材料价格", "盈利能力"])
    if "收入" in query or "营收" in query or "营业收入" in query:
        terms.extend(["营业收入", "同比增长", "主要会计数据", "revenue", "net revenue"])
    if "宏观" in query or "行业" in query:
        terms.extend(["宏观消费", "行业竞争", "供应链", "需求变化"])
    return _unique(terms)


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


def _unique(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
