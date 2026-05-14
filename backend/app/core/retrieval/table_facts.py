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
    "台积电": ("台积电", "tsmc", "2330"),
}
METRIC_ALIASES = {
    "revenue": ("总营收", "营业收入", "营收", "收入", "revenue", "net revenue", "total revenue"),
    "gross_profit": ("gross profit", "毛利"),
    "operating_income": ("operating income", "营业利润"),
    "net_income": ("净利润", "net income"),
    "eps_diluted": ("eps", "每股收益", "diluted", "稀释"),
}
QUARTER_ALIASES = {
    "q1": ("q1", "第一季度", "一季度"),
    "q2": ("q2", "第二季度", "二季度"),
    "q3": ("q3", "第三季度", "三季度", "前三季度"),
    "q4": ("q4", "第四季度", "四季度"),
}
QUARTER_PERIOD_HINTS = {
    "q1": ("first quarter", "three months ended", "第一季度", "一季度", "本报告期", "本期"),
    "q2": ("second quarter", "three months ended", "第二季度", "二季度", "半年度", "本报告期", "本期"),
    "q3": ("third quarter", "three months ended", "第三季度", "三季度", "本报告期", "本期"),
    "q4": ("fourth quarter", "three months ended", "第四季度", "四季度", "年度", "本报告期", "本期"),
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
    latest_requested = _latest_requested(lowered)
    if not requested_metric or not requested_companies:
        return []
    matches: list[TableFactMatch] = []
    fact_items = list(facts if facts is not None else load_table_facts())
    total_metric_requested = any(term in lowered for term in ("总营收", "total revenue"))
    latest_source_key = _latest_fact_source_key(fact_items, requested_companies, requested_metric) if latest_requested and not requested_years else None
    for fact in fact_items:
        if fact.get("metric") != requested_metric:
            continue
        if _is_percentage_fact(fact):
            continue
        if latest_source_key is not None and _source_sort_key(str(fact.get("source_pdf_name") or "")) != latest_source_key:
            continue
        if latest_source_key is not None and not _is_latest_period_fact(fact, fact_items):
            continue
        raw_value = str(fact.get("raw_value") or "")
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
        score += 0.2
        metric_label = str(fact.get("metric_label") or "").lower()
        if total_metric_requested and ("total" in metric_label or metric_label == "revenue"):
            score += 1.0
            reasons.append("total_metric")
        if total_metric_requested and _is_total_metric_fact(fact, fact_items):
            score += 2.5
            reasons.append("total_value")
        year_matched = False
        for year in requested_years:
            if year in period_label:
                score += 3.0
                reasons.append(f"period_year:{year}")
                year_matched = True
            elif f"fy{year}" in source_name.lower():
                score += 3.0
                reasons.append(f"fiscal_year:{year}")
                year_matched = True
        if requested_years and not year_matched:
            continue
        if latest_source_key is not None:
            score += 4.0
            reasons.append("latest_source")
        quarter_matched = False
        if requested_quarter and _quarter_matches(requested_quarter, haystack):
            score += 2.0
            reasons.append(f"quarter:{requested_quarter}")
            quarter_matched = True
        current_period_matched = bool(
            requested_quarter
            and _current_period_fact(fact, requested_quarter)
            and _is_latest_period_fact(fact, fact_items)
        )
        if current_period_matched:
            score += 3.0
            reasons.append("current_period")
        if requested_quarter and not current_period_matched and "前三季度" not in query:
            continue
        if (not requested_years or year_matched) and (not requested_quarter or quarter_matched or current_period_matched):
            reasons.append("strict_period_match")
        if latest_requested:
            period_rank = _global_latest_period_rank(fact, fact_items)
            if period_rank == 0:
                score += 4.0
                reasons.append("latest_period")
            elif period_rank == 1:
                score += 1.0
                reasons.append("recent_period")
        if requested_quarter == "q3" and "前三季度" in query and any(marker in haystack for marker in ("前三季度", "1-9", "nine months")):
            score += 1.5
            reasons.append("nine_months")
        if score >= 7.0:
            matches.append(TableFactMatch(fact=fact, score=score, reasons=reasons))
    return sorted(matches, key=lambda item: (-item.score, _fact_sort_key(item.fact, requested_quarter, latest_requested)))[:top_k]


def is_table_metric_query(query: str) -> bool:
    lowered = query.lower()
    return bool(_requested_metric(lowered) and _requested_companies(lowered))


def is_table_fact_period_compatible(query: str, fact: dict[str, Any]) -> bool:
    lowered = query.lower()
    requested_years = set(re.findall(r"20\d{2}", lowered))
    if not requested_years:
        return True
    haystack = " ".join(
        str(fact.get(field) or "")
        for field in ("period_label", "source_pdf_name", "source", "title", "date")
    ).lower()
    return any(year in haystack for year in requested_years)



def _latest_fact_source_key(facts: list[dict[str, Any]], requested_companies: list[str], requested_metric: str) -> tuple[int, int, int] | None:
    keys = [
        _source_sort_key(str(fact.get("source_pdf_name") or ""))
        for fact in facts
        if fact.get("metric") == requested_metric
        and not _is_percentage_fact(fact)
        and any(_company_matches(str(fact.get("company") or ""), str(fact.get("source_pdf_name") or ""), requested) for requested in requested_companies)
    ]
    return max(keys) if keys else None


def _source_sort_key(source_name: str) -> tuple[int, int, int]:
    match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", source_name)
    if match:
        return tuple(int(part) for part in match.groups())
    fiscal_match = re.search(r"fy(20\d{2})", source_name.lower())
    if fiscal_match:
        return (int(fiscal_match.group(1)), 12, 31)
    return (0, 0, 0)


def _is_percentage_fact(fact: dict[str, Any]) -> bool:
    return "%" in str(fact.get("raw_value") or "") or "%" in str(fact.get("period_label") or "")

def _is_latest_period_fact(fact: dict[str, Any], facts: list[dict[str, Any]]) -> bool:
    period_key = _period_sort_key(str(fact.get("period_label") or ""))
    if period_key is None:
        return True
    comparable = [
        _period_sort_key(str(other.get("period_label") or ""))
        for other in facts
        if other.get("table_id") == fact.get("table_id")
        and other.get("metric") == fact.get("metric")
        and str(other.get("metric_label") or "").lower() == str(fact.get("metric_label") or "").lower()
        and not _is_percentage_fact(other)
    ]
    comparable = [item for item in comparable if item is not None]
    return not comparable or period_key == max(comparable)


def _latest_requested(lowered_query: str) -> bool:
    return any(term in lowered_query for term in ("最新", "最近", "近期", "latest", "most recent"))


def _global_latest_period_rank(fact: dict[str, Any], facts: list[dict[str, Any]]) -> int | None:
    period_key = _period_sort_key(str(fact.get("period_label") or ""))
    if period_key is None:
        return None
    company = str(fact.get("company") or "")
    metric = fact.get("metric")
    comparable = sorted(
        {
            key
            for other in facts
            if str(other.get("company") or "") == company
            and other.get("metric") == metric
            and "%" not in str(other.get("raw_value") or "")
            for key in [_period_sort_key(str(other.get("period_label") or ""))]
            if key is not None
        },
        reverse=True,
    )
    try:
        return comparable.index(period_key)
    except ValueError:
        return None


def _period_sort_key(period_label: str) -> tuple[int, int, int] | None:
    match = re.search(r"(20\d{2})", period_label)
    if not match:
        return None
    year = int(match.group(1))
    month = 0
    day = 0
    month_match = re.search(r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})", period_label.lower())
    if month_match:
        month_name = month_match.group(0).split()[0][:3]
        month = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec").index(month_name) + 1
        day = int(month_match.group(1))
    return (year, month, day)

def _is_total_metric_fact(fact: dict[str, Any], facts: list[dict[str, Any]]) -> bool:
    metric_label = str(fact.get("metric_label") or "").lower()
    if "total" in metric_label or "合计" in metric_label:
        return True
    if metric_label != "revenue":
        return False
    try:
        column_index = int(fact.get("column_index") or 0)
        row_index = int(fact.get("row_index") or 0)
    except (TypeError, ValueError):
        return False
    same_group_columns = [
        int(other.get("column_index") or 0)
        for other in facts
        if other.get("table_id") == fact.get("table_id")
        and other.get("metric") == fact.get("metric")
        and str(other.get("metric_label") or "").lower() == metric_label
        and int(other.get("row_index") or 0) == row_index
        and str(other.get("period_label") or "") == str(fact.get("period_label") or "")
        and not _is_percentage_fact(other)
    ]
    return bool(same_group_columns) and column_index == max(same_group_columns)

def _requested_companies(lowered_query: str) -> list[str]:
    return [company for company, aliases in COMPANY_ALIASES.items() if any(_term_in_query(alias, lowered_query) for alias in aliases)]


def _requested_metric(lowered_query: str) -> str | None:
    for metric, aliases in METRIC_ALIASES.items():
        if any(_term_in_query(alias, lowered_query) for alias in aliases):
            return metric
    return None


def _requested_quarter(lowered_query: str) -> str | None:
    for quarter, aliases in QUARTER_ALIASES.items():
        if any(_term_in_query(alias, lowered_query) for alias in aliases):
            return quarter
    return None


def _term_in_query(term: str, lowered_query: str) -> bool:
    lowered_term = term.lower()
    if lowered_term.isascii() and lowered_term.replace("_", "").isalnum():
        return re.search(rf"(?<![a-z0-9]){re.escape(lowered_term)}(?![a-z0-9])", lowered_query) is not None
    return lowered_term in lowered_query


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
    return any(marker in haystack for marker in QUARTER_PERIOD_HINTS.get(quarter, ()))


def _current_period_fact(fact: dict[str, Any], requested_quarter: str) -> bool:
    if requested_quarter not in str(fact.get("source_pdf_name") or "").lower():
        return False
    if fact.get("metric") != "revenue":
        return False
    raw_value = str(fact.get("raw_value") or "")
    if "%" in raw_value:
        return False
    period_label = str(fact.get("period_label") or "").lower()
    metric_label = str(fact.get("metric_label") or "").lower()
    if requested_quarter == "q3" and "前三季度" in period_label:
        return False
    if any(marker in period_label for marker in QUARTER_PERIOD_HINTS.get(requested_quarter, ())):
        return True
    if metric_label in {"revenue", "total revenue", "营业收入", "一、营业总收入"} and period_label in {"本期", "本报告期"}:
        return True
    return False


def _fact_sort_key(fact: dict[str, Any], requested_quarter: str | None, latest_requested: bool = False) -> tuple[Any, ...]:
    source_name = str(fact.get("source_pdf_name") or "")
    period_label = str(fact.get("period_label") or "")
    metric_label = str(fact.get("metric_label") or "").lower()
    row_index = int(fact.get("row_index") or 0)
    current_rank = 0 if requested_quarter and _current_period_fact(fact, requested_quarter) else 1
    period_key = _period_sort_key(period_label) if latest_requested else None
    latest_rank = tuple(-part for part in period_key) if period_key else (0, 0, 0)
    metric_rank = 0 if row_index == 0 and metric_label == "revenue" else 1 if metric_label == "total revenue" else 2
    pct_rank = 1 if "%" in str(fact.get("raw_value") or "") else 0
    return (
        current_rank,
        metric_rank,
        pct_rank,
        latest_rank,
        source_name,
        period_label,
        str(fact.get("fact_id") or ""),
        int(fact.get("column_index") or 0),
    )
