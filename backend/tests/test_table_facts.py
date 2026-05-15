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


def test_extract_table_facts_aligns_spacer_columns_and_preserves_cny_scale(tmp_path):
    document = Document(
        doc_id="doc-catl",
        company="宁德时代",
        company_aliases=["CATL", "300750"],
        doc_type="financial_report",
        title="CATL FY2024",
        date="2025-03-15",
        source="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
        content="",
    )
    table = {
        "table_id": "tbl-catl-summary",
        "collection": "reports",
        "source_pdf_name": "300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
        "source_pdf_path": "/source/CATL.pdf",
        "page_num": 9,
        "title": "主要会计数据和财务指标",
        "headers": ["项目", "Column 2", "2024年", "2023年", "本年比上年 增减", "Column 6", "2022年", "Column 8", "Column 9"],
        "rows": [["", "营业收入（千元）", "362,012,554", "400,917,045", "-9.70%", "328,593,988", "", "328,593,988", ""]],
        "markdown": "| 项目 | Column 2 | 2024年 | 2023年 | 本年比上年 增减 | Column 6 | 2022年 | Column 8 | Column 9 |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| | 营业收入（千元） | 362,012,554 | 400,917,045 | -9.70% | 328,593,988 | | 328,593,988 | |",
    }
    artifact = TableArtifact(table=table, json_path=tmp_path / "tbl-catl-summary.json")

    facts = extract_table_facts(raw_frontmatter={}, document=document, table_artifact=artifact)

    by_value = {fact["raw_value"]: fact for fact in facts}
    assert by_value["362,012,554"]["period_label"] == "2024年"
    assert by_value["400,917,045"]["period_label"] == "2023年"
    assert by_value["-9.70%"]["period_label"] == "本年比上年 增减"
    assert by_value["328,593,988"]["period_label"] == "2022年"
    assert by_value["362,012,554"]["currency"] == "CNY"
    assert by_value["362,012,554"]["unit"] == "CNY thousands"


def test_extract_table_facts_aligns_cninfo_amount_spacer_header(tmp_path):
    document = Document(
        doc_id="doc-catl",
        company="宁德时代",
        company_aliases=["CATL", "300750"],
        doc_type="financial_report",
        title="CATL FY2024",
        date="2025-03-15",
        source="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
        content="",
    )
    table = {
        "table_id": "tbl-catl-income",
        "source_pdf_name": "300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
        "page_num": 119,
        "title": "合并利润表",
        "headers": ["项目", "Column 2", "2024年度", "Column 4", "Column 5", "Column 6", "2023年度"],
        "rows": [["一、营业总收入", "362,012,554", "", "", "", "400,917,045", ""]],
        "markdown": "| 项目 | Column 2 | 2024年度 | Column 4 | Column 5 | Column 6 | 2023年度 |\n| --- | --- | --- | --- | --- | --- | --- |\n| 一、营业总收入 | 362,012,554 | | | | 400,917,045 | |",
    }
    artifact = TableArtifact(table=table, json_path=tmp_path / "tbl-catl-income.json")

    facts = extract_table_facts(raw_frontmatter={}, document=document, table_artifact=artifact)

    by_value = {fact["raw_value"]: fact for fact in facts}
    assert by_value["362,012,554"]["period_label"] == "2024年度"
    assert by_value["400,917,045"]["period_label"] == "2023年度"
