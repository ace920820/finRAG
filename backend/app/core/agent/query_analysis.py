from __future__ import annotations

from typing import List

from app.models.events import IntentDetectedEvent, QueryRewriteEvent
from app.models.schemas import QueryIntent


# Single source of truth for entity recognition + query expansion. Each entry
# maps a canonical entity to the trigger tokens that mention it and the
# expansion terms appended to the rewrite. Keep `triggers` lowercase-comparable
# but the strings themselves match the user-facing forms.
_ENTITIES: tuple[dict, ...] = (
    {
        "canonical": "贵州茅台",
        "triggers": ("贵州茅台", "茅台", "600519"),
        "expansions": ("贵州茅台", "茅台", "600519", "白酒", "营业收入", "同比增长"),
    },
    {
        "canonical": "宁德时代",
        "triggers": ("宁德时代", "CATL", "300750"),
        "expansions": ("宁德时代", "CATL", "300750", "动力电池", "新能源车", "经营风险"),
    },
    {
        "canonical": "英伟达",
        "triggers": ("英伟达", "NVIDIA", "NVDA"),
        "expansions": ("英伟达", "NVIDIA", "NVDA", "revenue", "net revenue", "Data Center"),
    },
    {
        "canonical": "美联储",
        "triggers": ("美联储", "加息"),
        "expansions": (),
    },
    {
        "canonical": "新能源板块",
        "triggers": ("新能源", "动力电池"),
        "expansions": (),
    },
)

_REASONING_HINTS = ("对比", "比较", "传导", "影响", "宏观", "行业", "为什么", "如何")
_ANALYTICAL_HINTS = ("风险", "分析", "潜在", "趋势", "逻辑", "判断", "原因", "机会")
_FACTUAL_HINTS = ("多少", "是多少", "同比", "增长率", "收入", "营收", "净利润", "数据")


def _matched_entities(query: str) -> List[dict]:
    return [entity for entity in _ENTITIES if any(trigger in query for trigger in entity["triggers"])]


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
    return _unique([entity["canonical"] for entity in _matched_entities(query)])


def _expand_terms(query: str) -> List[str]:
    terms: List[str] = []
    for entity in _matched_entities(query):
        terms.extend(entity["expansions"])
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
