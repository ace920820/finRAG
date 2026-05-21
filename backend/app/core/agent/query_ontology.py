from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

COMPANY_ALIASES = {
    "NVIDIA": ("nvidia", "英伟达", "nvda"),
    "贵州茅台": ("贵州茅台", "茅台", "600519", "moutai"),
    "宁德时代": ("宁德时代", "catl", "300750"),
    "台积电": ("台积电", "tsmc", "2330"),
}

METRIC_ALIASES = {
    "revenue": ("总营收", "营业收入", "营收", "收入", "revenue", "net revenue", "total revenue"),
    "gross_profit": ("gross profit", "毛利"),
    "gross_margin": ("gross margin", "毛利率"),
    "operating_income": ("operating income", "营业利润"),
    "net_income": ("净利润", "net income"),
    "eps_diluted": ("eps", "每股收益", "diluted", "稀释"),
    "yoy_change": ("同比", "变化", "增长", "下降", "yoy", "change"),
}

QUARTER_ALIASES = {
    "q1": ("q1", "第一季度", "一季度"),
    "q2": ("q2", "第二季度", "二季度"),
    "q3": ("q3", "第三季度", "三季度", "前三季度"),
    "q4": ("q4", "第四季度", "四季度"),
}

FULL_WIDTH_TRANSLATION = str.maketrans(
    {
        ord("０") + index: str(index) for index in range(10)
    }
    | {
        ord("Ａ") + index: chr(ord("a") + index) for index in range(26)
    }
    | {
        ord("ａ") + index: chr(ord("a") + index) for index in range(26)
    }
)
PUNCTUATION_TRANSLATION = str.maketrans({
    "，": " ",
    "。": " ",
    "、": " ",
    "？": " ",
    "！": " ",
    "：": " ",
    "；": " ",
    "（": " ",
    "）": " ",
    "【": " ",
    "】": " ",
    "—": " ",
    "－": " ",
    "／": " ",
    "/": " ",
    "-": " ",
    ",": " ",
    ".": " ",
    ":": " ",
    ";": " ",
    "(": " ",
    ")": " ",
})


def normalize_query(query: str) -> str:
    text = unicodedata.normalize("NFKC", query).strip()
    text = text.translate(PUNCTUATION_TRANSLATION)
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def _normalize_match_text(text: str) -> str:
    return normalize_query(text)


@dataclass(frozen=True)
class MatchResult:
    canonical: str
    aliases: list[str]
    match: str


class _StdlibMatcher:
    def __init__(self, ontology: dict[str, tuple[str, ...]]):
        self._items = [
            (canonical, sorted({alias for alias in aliases}, key=lambda alias: (-len(_normalize_match_text(alias)), alias.lower())))
            for canonical, aliases in ontology.items()
        ]

    def match(self, normalized_query: str) -> list[MatchResult]:
        results: list[MatchResult] = []
        for canonical, aliases in sorted(self._items, key=lambda item: max((len(_normalize_match_text(alias)) for alias in item[1]), default=0), reverse=True):
            for alias in aliases:
                alias_norm = _normalize_match_text(alias)
                if alias_norm and alias_norm in normalized_query:
                    results.append(MatchResult(canonical=canonical, aliases=list(aliases), match=alias))
                    break
        return results


class OntologyMatcher:
    def __init__(self):
        self._company_backend = self._build_backend(COMPANY_ALIASES)
        self._metric_backend = self._build_backend(METRIC_ALIASES)

    def _build_backend(self, ontology: dict[str, tuple[str, ...]]):
        try:
            from flashtext import KeywordProcessor  # type: ignore
        except Exception:
            return _StdlibMatcher(ontology)
        processor = KeywordProcessor(case_sensitive=False)
        for canonical, aliases in ontology.items():
            for alias in aliases:
                processor.add_keyword(alias, (canonical, list(aliases), alias))
        return processor

    def _match(self, backend: Any, ontology: dict[str, tuple[str, ...]], normalized_query: str) -> list[dict[str, Any]]:
        if isinstance(backend, _StdlibMatcher):
            return [result.__dict__ for result in backend.match(normalized_query)]
        try:
            matches = backend.extract_keywords(normalized_query, span_info=False)
        except TypeError:
            matches = backend.extract_keywords(normalized_query)
        seen: set[tuple[str, str]] = set()
        results: list[dict[str, Any]] = []
        for match in matches:
            if isinstance(match, tuple) and len(match) == 3:
                canonical, aliases, alias = match
            else:
                canonical = str(match)
                aliases = list(ontology.get(canonical, ()))
                alias = canonical
            key = (canonical, alias)
            if key in seen:
                continue
            seen.add(key)
            results.append({"canonical": canonical, "aliases": list(aliases), "match": alias})
        return results

    def match_companies(self, normalized_query: str) -> list[dict[str, Any]]:
        return self._match(self._company_backend, COMPANY_ALIASES, normalized_query)

    def match_metrics(self, normalized_query: str) -> list[dict[str, Any]]:
        return self._match(self._metric_backend, METRIC_ALIASES, normalized_query)


_DEFAULT_MATCHER = OntologyMatcher()


def match_companies(normalized_query: str) -> list[dict[str, Any]]:
    return _DEFAULT_MATCHER.match_companies(normalized_query)


def match_metrics(normalized_query: str) -> list[dict[str, Any]]:
    return _DEFAULT_MATCHER.match_metrics(normalized_query)
