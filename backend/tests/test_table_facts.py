from __future__ import annotations

from pathlib import Path

from app.core.ingestion.table_facts import TableArtifact, extract_table_facts, parse_number
from app.models.schemas import Document


def test_parse_number_handles_financial_formats():
    assert parse_number("57,006") == 57006
    assert parse_number("(259)") == -259
    assert parse_number("4.90") == 4.9
    assert parse_number("—") is None
    assert parse_number("not a number") is None


def test_extract_table_facts_is_deterministic_and_traceable(tmp_path):
    document = Document(
        doc_id="doc-nvda",
        company="NVIDIA",
        company_aliases=["NVDA"],
        doc_type="financial_report",
        title="NVDA 10-Q",
        date="2025-11-19",
        source="NVDA_nvidia_10q_FY2026Q3_2025-11-19_q4cdn.pdf",
        content="",
    )
    table = {
        "table_id": "tbl-income",
        "collection": "reports",
        "source_pdf_name": "NVDA_nvidia_10q_FY2026Q3_2025-11-19_q4cdn.pdf",
        "source_pdf_path": "/source/NVDA.pdf",
        "page_num": 3,
        "title": "Condensed Consolidated Statements of Income",
        "headers": ["Metric", "Three Months Ended Oct 26 2025", "Three Months Ended Oct 27 2024"],
        "rows": [["Revenue", "57,006", "35,082"], ["Cost of revenue", "15,157", "8,926"]],
        "markdown": "| Metric | Three Months Ended Oct 26 2025 | Three Months Ended Oct 27 2024 |\n| --- | --- | --- |\n| Revenue | 57,006 | 35,082 |",
    }
    artifact = TableArtifact(table=table, json_path=tmp_path / "tbl-income.json")

    first = extract_table_facts(raw_frontmatter={}, document=document, table_artifact=artifact)
    second = extract_table_facts(raw_frontmatter={}, document=document, table_artifact=artifact)

    assert first == second
    assert len(first) == 2
    assert first[0]["fact_id"].startswith("fact-")
    assert first[0]["metric"] == "revenue"
    assert first[0]["value"] == 57006
    assert first[0]["period_label"] == "Three Months Ended Oct 26 2025"
    assert first[0]["doc_id"] == "doc-nvda"
    assert first[0]["table_id"] == "tbl-income"
    assert first[0]["page_num"] == 3
    assert first[0]["currency"] == "USD"
    assert first[0]["unit"] == "USD millions"
