from __future__ import annotations

from pathlib import Path

from app.core.retrieval.table_facts import load_table_facts, query_table_facts


def _fact(**overrides):
    fact = {
        "fact_id": "fact-fixture",
        "company": "NVIDIA",
        "metric": "revenue",
        "metric_label": "Revenue",
        "period_label": "FY2026 Q3 three months ended",
        "raw_value": "57,006",
        "value": 57006,
        "source_pdf_name": "NVDA_nvidia_10q_FY2026Q3_2025-11-19.pdf",
        "row_index": 0,
        "column_index": 0,
    }
    fact.update(overrides)
    return fact


def test_load_table_facts_handles_missing_file(tmp_path):
    assert load_table_facts(tmp_path / "missing.json") == []


def test_query_table_facts_matches_nvidia_q3_revenue():
    matches = query_table_facts("英伟达2026年第三季度的总营收是多少？", facts=[_fact()], top_k=5)

    assert matches
    assert matches[0].fact["company"] == "NVIDIA"
    assert matches[0].fact["metric"] == "revenue"
    assert matches[0].fact["raw_value"] == "57,006"
    assert "current_period" in matches[0].reasons


def test_query_table_facts_rejects_percentage_revenue_value():
    matches = query_table_facts(
        "英伟达2026年第三季度的总营收是多少？",
        facts=[_fact(raw_value="12%", value=12)],
    )

    assert matches == []


def test_query_table_facts_rejects_mismatched_requested_year():
    matches = query_table_facts(
        "英伟达2024年第三季度的总营收是多少？",
        facts=[_fact(period_label="FY2026 Q3 three months ended")],
    )

    assert matches == []


def test_query_table_facts_does_not_use_source_fy_when_period_has_different_year():
    matches = query_table_facts(
        "宁德时代2024年营业收入是多少？",
        facts=[
            _fact(
                fact_id="catl-2023-in-fy2024-file",
                company="宁德时代",
                metric_label="营业收入（千元）",
                period_label="2023年",
                raw_value="400,917,045",
                value=400917045,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
            )
        ],
    )

    assert matches == []


def test_query_table_facts_prefers_requested_annual_summary_fact_over_conflicts():
    matches = query_table_facts(
        "宁德时代2024年营业收入是多少？同比变化如何？",
        facts=[
            _fact(
                fact_id="catl-2024-parent-only",
                company="宁德时代",
                metric_label="一、营业收入",
                period_label="2024年度",
                raw_value="222,629,450",
                value=222629450,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
                page_num=121,
                table_id="tbl-parent-income",
            ),
            _fact(
                fact_id="catl-2024-summary",
                company="宁德时代",
                metric_label="营业收入（千元）",
                period_label="2024年",
                raw_value="362,012,554",
                value=362012554,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
                page_num=9,
                table_id="tbl-annual-summary",
            ),
            _fact(
                fact_id="catl-2023-summary",
                company="宁德时代",
                metric_label="营业收入（千元）",
                period_label="2023年",
                raw_value="400,917,045",
                value=400917045,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
                page_num=9,
                table_id="tbl-annual-summary",
            ),
        ],
        top_k=5,
    )

    assert matches
    assert matches[0].fact["fact_id"] == "catl-2024-summary"
    assert all(match.fact["fact_id"] != "catl-2023-summary" for match in matches)


def test_query_table_facts_includes_yoy_percentage_when_change_requested():
    matches = query_table_facts(
        "宁德时代2024年营业收入是多少？同比变化如何？",
        facts=[
            _fact(
                fact_id="catl-2024-revenue",
                company="宁德时代",
                metric_label="营业收入（千元）",
                period_label="2024年",
                raw_value="362,012,554",
                value=362012554,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
            ),
            _fact(
                fact_id="catl-2024-yoy",
                company="宁德时代",
                metric_label="营业收入（千元）",
                period_label="本年比上年 增减",
                raw_value="-9.70%",
                value=-9.7,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
            ),
        ],
        top_k=5,
    )

    assert [match.fact["fact_id"] for match in matches] == ["catl-2024-revenue", "catl-2024-yoy"]


def test_query_table_facts_filters_quarter_and_ratio_for_annual_query():
    matches = query_table_facts(
        "宁德时代2024年营业收入是多少？同比变化如何？",
        facts=[
            _fact(
                fact_id="catl-annual",
                company="宁德时代",
                metric_label="营业收入（千元）",
                period_label="2024年",
                raw_value="362,012,554",
                value=362012554,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
            ),
            _fact(
                fact_id="catl-q1",
                company="宁德时代",
                metric_label="营业收入",
                period_label="2024年1-3月",
                raw_value="7,977,077.86",
                value=7977077.86,
                source_pdf_name="300750SZ_catl_quarterly_report_2024Q1_2024-04-16_cninfo.pdf",
            ),
            _fact(
                fact_id="catl-ratio",
                company="宁德时代",
                metric_label="营业收入合计",
                period_label="2024年",
                raw_value="100.00%",
                value=100,
                source_pdf_name="300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf",
            ),
        ],
        top_k=5,
    )

    assert [match.fact["fact_id"] for match in matches] == ["catl-annual"]


def test_query_table_facts_current_period_uses_period_header_not_nvidia_column_index():
    matches = query_table_facts(
        "英伟达2026年第三季度的总营收是多少？",
        facts=[_fact(column_index=1, period_label="FY2026 Q3 three months ended")],
    )

    assert matches
    assert "current_period" in matches[0].reasons


def test_query_table_facts_rejects_wrong_company():
    matches = query_table_facts(
        "台积电2024年营业收入是多少？",
        facts=[{"company": "NVIDIA", "metric": "revenue", "raw_value": "1", "value": 1}],
    )

    assert matches == []


def test_query_table_facts_matches_moutai_annual_revenue():
    matches = query_table_facts(
        "贵州茅台2024年营业收入是多少？",
        facts=[
            _fact(
                company="贵州茅台",
                metric_label="营业收入",
                period_label="2024年",
                raw_value="170,899,152,276.34",
                value=170899152276.34,
                source_pdf_name="贵州茅台2024年年度报告.pdf",
            )
        ],
        top_k=5,
    )

    assert matches
    assert matches[0].fact["company"] == "贵州茅台"
    assert matches[0].fact["metric"] == "revenue"
    assert matches[0].fact["period_label"] in {"2024年", "2024年度"}
    assert matches[0].fact["raw_value"] == "170,899,152,276.34"


def test_query_table_facts_prefers_latest_period_for_generic_latest_query():
    matches = query_table_facts(
        "贵州茅台最新的营收数据",
        facts=[
            _fact(
                fact_id="moutai-2024-annual",
                company="贵州茅台",
                metric_label="一、营业收入",
                period_label="2024年度",
                raw_value="94,526,736,836.41",
                value=94526736836.41,
                source_pdf_name="600519SH_moutai_annual_report_FY2024_2025-04-03_cninfo.pdf",
            ),
            _fact(
                fact_id="moutai-2026-q1",
                company="贵州茅台",
                metric_label="一、营业总收入",
                period_label="2026年第一季度",
                raw_value="54,702,912,385.23",
                value=54702912385.23,
                source_pdf_name="600519SH_moutai_quarterly_report_2026Q1_2026-04-25_cninfo.pdf",
            ),
        ],
        top_k=5,
    )

    assert matches
    assert matches[0].fact["fact_id"] == "moutai-2026-q1"
    assert "latest_period" in matches[0].reasons
