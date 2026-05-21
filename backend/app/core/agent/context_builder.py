from __future__ import annotations

import re
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field


class EvidencePackItem(BaseModel):
    citation_id: int
    chunk_id: str
    title: str
    doc_type: str
    company: str
    date: str
    page: Optional[int] = None
    source: Optional[str] = None
    section: Optional[str] = None
    content: str
    compact_content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    preserved_fields: dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    items: list[EvidencePackItem] = Field(default_factory=list)
    original_count: int = 0
    compressed_count: int = 0
    dropped_duplicate_count: int = 0


def build_evidence_pack(items: Sequence[object], text_limit: int = 700) -> EvidencePack:
    seen: set[tuple[Any, ...]] = set()
    packed: list[EvidencePackItem] = []
    for item in items:
        key = _dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        packed.append(_pack_item(item, text_limit=text_limit))
    return EvidencePack(
        items=packed,
        original_count=len(items),
        compressed_count=len(packed),
        dropped_duplicate_count=len(items) - len(packed),
    )


def _pack_item(item: object, text_limit: int) -> EvidencePackItem:
    metadata = dict(getattr(item, "metadata", {}) or {})
    content = str(getattr(item, "content", None) or getattr(item, "preview", "") or "")
    preserved_fields = _preserved_fields(item, metadata)
    compact_content = _compact_table_fact(preserved_fields) if metadata.get("chunk_type") == "table_fact" else _compact_text(content, text_limit)
    return EvidencePackItem(
        citation_id=int(getattr(item, "citation_id", 0)),
        chunk_id=str(getattr(item, "chunk_id")),
        title=str(getattr(item, "title")),
        doc_type=str(getattr(item, "doc_type")),
        company=str(getattr(item, "company")),
        date=str(getattr(item, "date")),
        page=getattr(item, "page", None),
        source=str(metadata.get("source") or metadata.get("source_pdf_name") or getattr(item, "title")),
        section=str(metadata.get("section") or metadata.get("table_id") or "") or None,
        content=content,
        compact_content=compact_content,
        metadata=metadata,
        preserved_fields=preserved_fields,
    )


def _dedupe_key(item: object) -> tuple[Any, ...]:
    metadata = dict(getattr(item, "metadata", {}) or {})
    chunk_id = str(getattr(item, "chunk_id", "") or "")
    if chunk_id:
        return ("chunk", chunk_id)
    if metadata.get("chunk_type") == "table_fact":
        return (
            "table_fact",
            metadata.get("source_pdf_name") or metadata.get("source") or getattr(item, "title", ""),
            metadata.get("table_id"),
            metadata.get("metric"),
            metadata.get("period_label"),
            metadata.get("raw_value"),
        )
    content = str(getattr(item, "content", None) or getattr(item, "preview", "") or "")
    return (
        "text",
        getattr(item, "title", ""),
        getattr(item, "page", None),
        _normalize_text(content)[:160],
    )


def _preserved_fields(item: object, metadata: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "raw_value",
        "value",
        "unit",
        "currency",
        "period_label",
        "metric",
        "metric_label",
        "table_id",
        "page_num",
        "source_pdf_name",
        "source",
    )
    preserved = {key: metadata[key] for key in keys if metadata.get(key) not in (None, "")}
    if getattr(item, "page", None) is not None:
        preserved.setdefault("page", getattr(item, "page"))
    return preserved


def _compact_table_fact(fields: dict[str, Any]) -> str:
    parts = [
        f"metric={fields.get('metric_label') or fields.get('metric') or 'unknown'}",
        f"value={fields.get('raw_value') or fields.get('value') or 'unknown'}",
        f"period={fields.get('period_label') or 'unknown'}",
        f"unit={fields.get('unit') or 'unknown'}",
        f"currency={fields.get('currency') or 'unknown'}",
        f"table={fields.get('table_id') or 'unknown'}",
        f"source={fields.get('source_pdf_name') or fields.get('source') or 'unknown'}",
    ]
    if fields.get("page") or fields.get("page_num"):
        parts.append(f"page={fields.get('page') or fields.get('page_num')}")
    return " | ".join(parts)


def _compact_text(content: str, text_limit: int) -> str:
    normalized = re.sub(r"\s+", " ", content).strip()
    if len(normalized) <= text_limit:
        return normalized
    return normalized[: max(0, text_limit - 3)].rstrip() + "..."


def _normalize_text(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip().lower()
