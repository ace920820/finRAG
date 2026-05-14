from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from pathlib import Path
from typing import Any

from app.models.schemas import Chunk, Document


CORE_METRICS = {
    "revenue": (
        "total revenue",
        "revenue",
        "营业总收入",
        "营业收入",
    ),
    "gross_profit": ("gross profit", "毛利"),
    "operating_income": ("operating income", "营业利润"),
    "net_income": ("net income", "净利润"),
    "eps_diluted": ("diluted", "稀释每股收益"),
}
NUMERIC_RE = re.compile(r"^-?\(?[$￥¥NT\s]*[\d,]+(?:\.\d+)?\)?%?$")


@dataclass(frozen=True)
class TableArtifact:
    table: dict[str, Any]
    json_path: Path


def build_table_row_chunks(
    *,
    raw_frontmatter: dict[str, str],
    document: Document,
    table_artifact: TableArtifact,
    start_index: int,
) -> list[Chunk]:
    rows = _rows(table_artifact.table)
    if not _is_financial_table(table_artifact.table, rows):
        return []

    chunks: list[Chunk] = []
    for row_index, row in enumerate(rows):
        label = _row_label(row)
        metric = normalize_metric(label)
        if metric is None:
            continue
        content = _render_row_content(table_artifact.table, row, label, metric)
        table_id = _table_id(table_artifact)
        chunk_hash = _hash_text(f"{document.doc_id}:{table_id}:row:{row_index}:{content}")[:12]
        metadata = _base_table_metadata(raw_frontmatter, document, table_artifact)
        metadata.update(
            {
                "chunk_type": "table_row",
                "row_index": row_index,
                "metric": metric,
                "metric_label": label,
                "statement_type": _statement_type(table_artifact.table, label),
                "unit": _infer_unit(document, table_artifact.table),
                "currency": _infer_currency(document, table_artifact.table),
            }
        )
        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}-tr{row_index:04d}-{chunk_hash}",
                doc_id=document.doc_id,
                section=f"table:{table_id}:row:{row_index}",
                page_num=_safe_int(table_artifact.table.get("page_num")),
                chunk_index=start_index + len(chunks),
                content=content,
                metadata=metadata,
            )
        )
    return chunks


def extract_table_facts(*, raw_frontmatter: dict[str, str], document: Document, table_artifact: TableArtifact) -> list[dict[str, Any]]:
    rows = _rows(table_artifact.table)
    if not _is_financial_table(table_artifact.table, rows):
        return []
    facts: list[dict[str, Any]] = []
    headers = [str(item).strip() for item in table_artifact.table.get("headers") or []]
    table_id = _table_id(table_artifact)
    currency = _infer_currency(document, table_artifact.table)
    unit = _infer_unit(document, table_artifact.table)

    for row_index, row in enumerate(rows):
        label = _row_label(row)
        metric = normalize_metric(label)
        if metric is None:
            continue
        for column_index, raw_value in _numeric_cells(row):
            value = parse_number(raw_value)
            fact_seed = ":".join(
                [document.doc_id, table_id, metric, str(row_index), str(column_index), str(raw_value)]
            )
            facts.append(
                {
                    "fact_id": f"fact-{_hash_text(fact_seed)[:16]}",
                    "doc_id": document.doc_id,
                    "table_id": table_id,
                    "company": document.company,
                    "doc_type": document.doc_type,
                    "source_pdf_name": str(table_artifact.table.get("source_pdf_name") or document.source),
                    "source_pdf_path": str(table_artifact.table.get("source_pdf_path") or raw_frontmatter.get("source_pdf_path") or ""),
                    "page_num": _safe_int(table_artifact.table.get("page_num")),
                    "statement_type": _statement_type(table_artifact.table, label),
                    "metric": metric,
                    "metric_label": label,
                    "period_label": headers[column_index] if column_index < len(headers) else f"column_{column_index + 1}",
                    "value": value,
                    "raw_value": str(raw_value),
                    "unit": unit,
                    "currency": currency,
                    "collection": str(table_artifact.table.get("collection") or raw_frontmatter.get("collection") or "default"),
                    "row_index": row_index,
                    "column_index": column_index,
                    "table_json_path": str(table_artifact.json_path),
                }
            )
    return facts


def normalize_metric(label: str) -> str | None:
    lowered = label.lower().replace("：", "").strip()
    compact = re.sub(r"\s+", " ", lowered)
    for metric, aliases in CORE_METRICS.items():
        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower == compact or alias_lower in compact:
                if metric == "revenue" and "cost of revenue" in compact:
                    return None
                if metric == "net_income" and "per share" in compact:
                    return None
                return metric
    return None


def parse_number(value: str) -> float | int | None:
    text = str(value).strip()
    if not text or text in {"—", "-", "--"}:
        return None
    if not NUMERIC_RE.match(text):
        return None
    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()$￥¥NT ").replace(",", "").replace("%", "")
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    if negative:
        parsed = -parsed
    return int(parsed) if parsed.is_integer() else parsed


def _rows(table: dict[str, Any]) -> list[list[str]]:
    rows = table.get("rows") or []
    return [[str(cell).strip() for cell in row] for row in rows if isinstance(row, list)]


def _row_label(row: list[str]) -> str:
    for cell in row:
        if cell and not parse_number(cell):
            return cell.strip()
    return row[0].strip() if row else ""


def _numeric_cells(row: list[str]) -> list[tuple[int, str]]:
    return [(index, cell) for index, cell in enumerate(row) if parse_number(cell) is not None]


def _is_financial_table(table: dict[str, Any], rows: list[list[str]]) -> bool:
    haystack = " ".join(
        [str(table.get("title") or ""), str(table.get("markdown") or ""), " ".join(" ".join(row) for row in rows[:30])]
    ).lower()
    return any(alias.lower() in haystack for aliases in CORE_METRICS.values() for alias in aliases)


def _render_row_content(table: dict[str, Any], row: list[str], label: str, metric: str) -> str:
    headers = [str(item).strip() for item in table.get("headers") or []]
    values = []
    for index, cell in enumerate(row):
        header = headers[index] if index < len(headers) and headers[index] else f"Column {index + 1}"
        if cell:
            values.append(f"{header}: {cell}")
    return "\n".join(
        [
            f"Table Row Metric: {metric}",
            f"Label: {label}",
            f"Table: {table.get('title') or table.get('table_id') or 'Table'}",
            f"Page: {table.get('page_num') if table.get('page_num') is not None else 'unknown'}",
            "Values: " + "; ".join(values),
        ]
    ).strip()


def _base_table_metadata(raw_frontmatter: dict[str, str], document: Document, table_artifact: TableArtifact) -> dict[str, Any]:
    table = table_artifact.table
    return {
        **raw_frontmatter,
        "title": document.title,
        "source": document.source,
        "company": document.company,
        "doc_type": document.doc_type,
        "date": document.date,
        "collection": str(table.get("collection") or raw_frontmatter.get("collection") or "default"),
        "source_name": str(table.get("source_pdf_name") or document.source),
        "table_id": _table_id(table_artifact),
        "table_title": str(table.get("title") or ""),
        "table_json_path": str(table_artifact.json_path),
        "table_csv_path": str(table.get("csv_path") or ""),
        "row_count": table.get("row_count", 0),
        "column_count": table.get("column_count", 0),
        "extraction_method": str(table.get("extraction_method") or "pdfplumber"),
    }


def _statement_type(table: dict[str, Any], label: str) -> str:
    text = f"{table.get('title') or ''} {label} {table.get('markdown') or ''}".lower()
    if any(marker in text for marker in ("income", "operations", "profit", "营收", "利润")):
        return "income_statement"
    return "unknown"


def _infer_currency(document: Document, table: dict[str, Any]) -> str:
    text = f"{document.company} {document.source} {table.get('source_pdf_name') or ''} {table.get('markdown') or ''}".lower()
    if "nvidia" in text or "nvda" in text or "$" in text:
        return "USD"
    if "tsmc" in text or "台积电" in text or "nt$" in text:
        return "TWD"
    if any(marker in text for marker in ("宁德时代", "贵州茅台", "rmb", "人民币", "cninfo")):
        return "CNY"
    return "unknown"


def _infer_unit(document: Document, table: dict[str, Any]) -> str:
    text = f"{document.company} {document.source} {table.get('source_pdf_name') or ''} {table.get('markdown') or ''}".lower()
    if "nvidia" in text or "nvda" in text:
        return "USD millions"
    if "tsmc" in text or "台积电" in text:
        return "TWD thousands"
    if any(marker in text for marker in ("宁德时代", "贵州茅台", "cninfo", "人民币")):
        return "CNY"
    return "unknown"


def _table_id(table_artifact: TableArtifact) -> str:
    return str(table_artifact.table.get("table_id") or table_artifact.json_path.stem)


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _hash_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()
