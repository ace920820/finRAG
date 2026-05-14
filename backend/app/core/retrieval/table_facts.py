from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Iterable

from app.core.config import get_settings


COMPANY_ALIASES = {
    "NVIDIA": ("nvidia", "英伟达", "nvda"),
    "贵州茅台": ("贵州茅台", "茅台", "600519", "moutai"),
    "宁德时代": ("宁德时代", "catl", "300750"),
    "台积电": ("台积电", "tsmc", "2330", "tsm"),
}
METRIC_ALIASES = {
    "revenue": ("总营收", "营业收入", "营收", "收入", "revenue", "net revenue", "total revenue"),
    "gross_profit": ("gross profit", "毛利"),
    "operating_income": ("operating income", "营业利润"),
    "net_income": ("净利润", "net income"),
    "eps_diluted": ("eps", "每股收益", "diluted", "稀释"),
}
QUARTER_ALIASES = {
    "q1": ("q1", "1q", "第一季度", "一季度"),
    "q2": ("q2", "2q", "第二季度", "二季度"),
    "q3": ("q3", "3q", "第三季度", "三季度", "前三季度"),
    "q4": ("q4", "4q", "第四季度", "四季度"),
}


@dataclass(frozen=True)
class TableFactMatch:
    fact: dict[str, Any]
    score: float
    reasons: list[str]


def load_table_facts(path: Path | None = None) -> list[dict[str, Any]]:
    facts_path = path or get_settings().processed_dir / "table_facts.json"
    try:
        payload = json.loads(facts_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def query_table_facts(query: str, facts: Iterable[dict[str, Any]] | None = None, top_k: int = 5) -> list[TableFactMatch]:
    lowered = query.lower()
    requested_companies = _requested_companies(lowered)
    requested_metric = _requested_metric(lowered)
    requested_years = set(re.findall(r"20\d{2}", lowered))
    requested_quarter = _requested_quarter(lowered)
    if not requested_metric or not requested_companies:
        return []
    matches: list[TableFactMatch] = []
    for fact in facts if facts is not None else load_table_facts():
        if fact.get("metric") != requested_metric:
            continue
        score = 0.0
        reasons: list[str] = []
        company = str(fact.get("company") or "")
        source_name = str(fact.get("source_pdf_name") or "")
        period_label = str(fact.get("period_label") or "")
        haystack = f"{company} {source_name} {period_label} {fact.get('metric_label') or ''}".lower()
        if any(_company_matches(company, source_name, requested) for requested in requested_companies):
            score += 4.0
            reasons.append("company")
        else:
            continue
        score += 3.0
        reasons.append("metric")
        if fact.get("value") is not None:
            score += 0.5
            reasons.append("value")
        raw_value = str(fact.get("raw_value") or "")
        if "%" not in raw_value:
            score += 0.2
        metric_label = str(fact.get("metric_label") or "").lower()
        if any(term in lowered for term in ("总营收", "total revenue")) and ("total" in metric_label or metric_label == "revenue"):
            score += 1.0
            reasons.append("total_metric")
        for year in requested_years:
            if year in str(fact.get("period_label") or ""):
                score += 3.0
                reasons.append(f"period_year:{year}")
            elif year in haystack:
                score += 1.0
                reasons.append(f"source_year:{year}")
        if requested_quarter and _quarter_matches(requested_quarter, haystack):
            score += 2.0
            reasons.append(f"quarter:{requested_quarter}")
        if requested_quarter and _current_period_fact(fact, requested_quarter):
            score += 3.0
            reasons.append("current_period")
        if requested_quarter == "q3" and "前三季度" in query and any(marker in haystack for marker in ("前三季度", "1-9", "nine months")):
            score += 1.5
            reasons.append("nine_months")
        if score >= 7.0:
            matches.append(TableFactMatch(fact=fact, score=score, reasons=reasons))
    return sorted(matches, key=lambda item: (-item.score, _fact_sort_key(item.fact, requested_quarter)))[:top_k]


def is_table_metric_query(query: str) -> bool:
    lowered = query.lower()
    return bool(_requested_metric(lowered) and _requested_companies(lowered))


def _requested_companies(lowered_query: str) -> list[str]:
    return [company for company, aliases in COMPANY_ALIASES.items() if any(alias in lowered_query for alias in aliases)]


def _requested_metric(lowered_query: str) -> str | None:
    for metric, aliases in METRIC_ALIASES.items():
        if any(alias in lowered_query for alias in aliases):
            return metric
    return None


def _requested_quarter(lowered_query: str) -> str | None:
    for quarter, aliases in QUARTER_ALIASES.items():
        if any(alias in lowered_query for alias in aliases):
            return quarter
    return None


def _company_matches(company: str, source_name: str, requested: str) -> bool:
    aliases = COMPANY_ALIASES.get(requested, (requested,))
    haystack = f"{company} {source_name}".lower()
    return company == requested or any(alias in haystack for alias in aliases)


def _quarter_matches(quarter: str, haystack: str) -> bool:
    if quarter in haystack:
        return True
    aliases = QUARTER_ALIASES.get(quarter, ())
    if any(alias in haystack for alias in aliases):
        return True
    if quarter == "q3":
        return any(marker in haystack for marker in ("third quarter", "three months ended", "nine months ended", "前三季度", "1-9月"))
    return False


def _current_period_fact(fact: dict[str, Any], requested_quarter: str) -> bool:
    if requested_quarter not in str(fact.get("source_pdf_name") or "").lower():
        return False
    if str(fact.get("metric_label") or "").lower() not in {"revenue", "total revenue", "营业收入", "一、营业总收入"}:
        return False
    column_index = int(fact.get("column_index") or 0)
    raw_value = str(fact.get("raw_value") or "")
    if requested_quarter == "q3":
        row_index = int(fact.get("row_index") or 0)
        metric_label = str(fact.get("metric_label") or "").lower()
        return ((row_index == 0 and metric_label == "revenue" and column_index == 6) or (metric_label == "total revenue" and column_index == 2)) and "%" not in raw_value
    return "%" not in raw_value


def _fact_sort_key(fact: dict[str, Any], requested_quarter: str | None) -> tuple[int, int, str, str, str, int]:
    source_name = str(fact.get("source_pdf_name") or "")
    period_label = str(fact.get("period_label") or "")
    metric_label = str(fact.get("metric_label") or "").lower()
    row_index = int(fact.get("row_index") or 0)
    current_rank = 0 if requested_quarter and _current_period_fact(fact, requested_quarter) else 1
    metric_rank = 0 if row_index == 0 and metric_label == "revenue" else 1 if metric_label == "total revenue" else 2
    return (
        current_rank,
        metric_rank,
        source_name,
        period_label,
        str(fact.get("fact_id") or ""),
        int(fact.get("column_index") or 0),
    )
