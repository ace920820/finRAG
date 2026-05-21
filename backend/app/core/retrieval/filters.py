from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from app.models.schemas import RetrievalPlan


@dataclass(frozen=True)
class MetadataFilterResult:
    filtered_items: list[object]
    filters: dict[str, object]
    before_count: int
    after_count: int
    relaxed: bool = False
    fallback_reason: Optional[str] = None


def build_metadata_filters(plan: Optional[RetrievalPlan]) -> dict[str, object]:
    if plan is None:
        return {}

    filters: dict[str, object] = {}
    if plan.filters.get("collection"):
        filters["collection"] = plan.filters["collection"]
    if plan.entities:
        filters["company"] = [entity.canonical for entity in plan.entities]
    if plan.preferred_doc_types:
        filters["doc_type"] = list(plan.preferred_doc_types)
    if plan.metrics:
        filters["metric"] = [metric.canonical for metric in plan.metrics]
    if plan.time_range and plan.time_range.year is not None:
        filters["year"] = plan.time_range.year
    if plan.time_range and plan.time_range.quarter:
        filters["quarter"] = plan.time_range.quarter
    if plan.retrieval_strategy == "table_fact_first":
        filters["chunk_type"] = ["table_fact", "table_row", "table"]
    elif plan.retrieval_strategy == "financial_report_first":
        filters["chunk_type"] = ["section", "table", "table_row", "table_fact", "text"]
    elif plan.retrieval_strategy == "research_report_analysis":
        filters["chunk_type"] = ["section", "text", "table", "table_row", "table_fact"]
    return filters


def apply_metadata_filters(items: Iterable[object], filters: dict[str, object], minimum_count: int = 1) -> MetadataFilterResult:
    candidates = list(items)
    before_count = len(candidates)
    if not filters:
        return MetadataFilterResult(filtered_items=candidates, filters={}, before_count=before_count, after_count=before_count)

    filtered = [item for item in candidates if _matches_filters(item, filters)]
    if len(filtered) >= minimum_count:
        return MetadataFilterResult(filtered_items=filtered, filters=filters, before_count=before_count, after_count=len(filtered))

    relaxed = [item for item in candidates if _matches_filters(item, _relax_filters(filters))]
    if relaxed:
        return MetadataFilterResult(
            filtered_items=relaxed,
            filters=_relax_filters(filters),
            before_count=before_count,
            after_count=len(relaxed),
            relaxed=True,
            fallback_reason="metadata_filters_relaxed",
        )

    return MetadataFilterResult(
        filtered_items=candidates,
        filters=filters,
        before_count=before_count,
        after_count=before_count,
        relaxed=True,
        fallback_reason="metadata_filters_relaxed_to_all",
    )


def _relax_filters(filters: dict[str, object]) -> dict[str, object]:
    relaxed = dict(filters)
    relaxed.pop("chunk_type", None)
    relaxed.pop("quarter", None)
    relaxed.pop("year", None)
    return relaxed


def _matches_filters(item: object, filters: dict[str, object]) -> bool:
    metadata = getattr(item, "metadata", {}) or {}
    for key, expected in filters.items():
        value = metadata.get(key)
        if key in {"company", "doc_type", "metric", "chunk_type", "collection"}:
            values = expected if isinstance(expected, list) else [expected]
            if value not in values:
                return False
        elif key == "year":
            if str(expected) not in str(metadata.get("period_label", "")) and str(expected) not in str(metadata.get("source_pdf_name", "")):
                return False
        elif key == "quarter":
            if str(expected).lower() not in str(metadata.get("period_label", "")).lower() and str(expected).lower() not in str(metadata.get("source_pdf_name", "")).lower():
                return False
    return True
