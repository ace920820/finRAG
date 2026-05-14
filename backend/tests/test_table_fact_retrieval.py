from __future__ import annotations

from pathlib import Path

from app.core.retrieval.table_facts import load_table_facts, query_table_facts


def test_load_table_facts_handles_missing_file(tmp_path):
    assert load_table_facts(tmp_path / "missing.json") == []


def test_query_table_facts_matches_nvidia_q3_revenue():
    matches = query_table_facts("英伟达2026年第三季度的总营收是多少？", top_k=5)

    assert matches
    assert matches[0].fact["company"] == "NVIDIA"
    assert matches[0].fact["metric"] == "revenue"
    assert matches[0].fact["raw_value"] == "57,006"
    assert "current_period" in matches[0].reasons


def test_query_table_facts_rejects_wrong_company():
    matches = query_table_facts(
        "台积电2024年营业收入是多少？",
        facts=[{"company": "NVIDIA", "metric": "revenue", "raw_value": "1", "value": 1}],
    )

    assert matches == []


def test_query_table_facts_matches_moutai_annual_revenue():
    matches = query_table_facts("贵州茅台2024年营业收入是多少？", top_k=5)

    assert matches
    assert matches[0].fact["company"] == "贵州茅台"
    assert matches[0].fact["metric"] == "revenue"
    assert matches[0].fact["period_label"] in {"2024年", "2024年度"}
    assert matches[0].fact["raw_value"] == "170,899,152,276.34"
