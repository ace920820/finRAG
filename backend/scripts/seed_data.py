from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULT_BASE_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "processed"
BASE_DIR = Path(os.environ.get("FINRAG_PROCESSED_DATA_DIR") or _DEFAULT_BASE_DIR)

DOCUMENTS = [
    {
        "doc_id": "d001",
        "company": "贵州茅台",
        "company_aliases": ["茅台", "600519", "贵州茅台酒"],
        "doc_type": "financial_report",
        "title": "贵州茅台 2023 年年度报告",
        "date": "2024-03-28",
        "source": "贵州茅台2023年报",
        "content": "贵州茅台2023年报摘要。",
    },
    {
        "doc_id": "d002",
        "company": "宁德时代",
        "company_aliases": ["CATL", "300750", "宁德时代新能源"],
        "doc_type": "financial_report",
        "title": "宁德时代 2023 年年度报告",
        "date": "2024-03-15",
        "source": "宁德时代2023年报",
        "content": "宁德时代2023年报摘要。",
    },
    {
        "doc_id": "d003",
        "company": "宁德时代",
        "company_aliases": ["CATL", "300750"],
        "doc_type": "research_report",
        "title": "宁德时代深度研究报告",
        "date": "2024-04-10",
        "source": "券商研报",
        "content": "宁德时代深度研究摘要。",
    },
    {
        "doc_id": "d004",
        "company": "宏观新闻",
        "company_aliases": ["美联储", "新能源", "A股"],
        "doc_type": "news",
        "title": "美联储加息与新能源板块新闻汇总",
        "date": "2024-04-12",
        "source": "新闻汇编",
        "content": "宏观与行业新闻摘要。",
    },
]

CHUNKS = [
    {
        "chunk_id": "c001",
        "doc_id": "d001",
        "section": "主要会计数据",
        "page_num": 23,
        "chunk_index": 0,
        "content": "贵州茅台2023年营业收入1505.60亿元，同比增长19.0%。",
        "embedding": [],
        "metadata": {"company": "贵州茅台", "doc_type": "financial_report", "date": "2024-03-28", "source": "贵州茅台2023年报"},
    },
    {
        "chunk_id": "c002",
        "doc_id": "d001",
        "section": "风险因素",
        "page_num": 88,
        "chunk_index": 1,
        "content": "渠道动销、宏观消费与库存管理存在不确定性。",
        "embedding": [],
        "metadata": {"company": "贵州茅台", "doc_type": "financial_report", "date": "2024-03-28", "source": "贵州茅台2023年报"},
    },
    {
        "chunk_id": "c003",
        "doc_id": "d002",
        "section": "主要会计数据",
        "page_num": 19,
        "chunk_index": 0,
        "content": "宁德时代2023年收入突破4000亿元，动力电池市场竞争加剧。",
        "embedding": [],
        "metadata": {"company": "宁德时代", "doc_type": "financial_report", "date": "2024-03-15", "source": "宁德时代2023年报"},
    },
    {
        "chunk_id": "c004",
        "doc_id": "d002",
        "section": "风险因素",
        "page_num": 104,
        "chunk_index": 1,
        "content": "原材料价格波动、海外政策变化与产能扩张节奏可能影响盈利能力。",
        "embedding": [],
        "metadata": {"company": "宁德时代", "doc_type": "financial_report", "date": "2024-03-15", "source": "宁德时代2023年报"},
    },
    {
        "chunk_id": "c005",
        "doc_id": "d003",
        "section": "投资逻辑",
        "page_num": 3,
        "chunk_index": 0,
        "content": "宁德时代在全球动力电池供应链中保持领先，海外客户拓展仍是核心变量。",
        "embedding": [],
        "metadata": {"company": "宁德时代", "doc_type": "research_report", "date": "2024-04-10", "source": "券商研报"},
    },
    {
        "chunk_id": "c006",
        "doc_id": "d003",
        "section": "风险提示",
        "page_num": 11,
        "chunk_index": 1,
        "content": "电池原材料价格波动和终端需求波动可能带来盈利预期下修。",
        "embedding": [],
        "metadata": {"company": "宁德时代", "doc_type": "research_report", "date": "2024-04-10", "source": "券商研报"},
    },
    {
        "chunk_id": "c007",
        "doc_id": "d004",
        "section": "新闻",
        "page_num": 1,
        "chunk_index": 0,
        "content": "市场关注美联储加息对新能源板块估值与融资成本的影响。",
        "embedding": [],
        "metadata": {"company": "宏观新闻", "doc_type": "news", "date": "2024-04-12", "source": "新闻汇编"},
    },
]

DEMO_CASES = [
    {
        "id": "demo-factual",
        "question": "贵州茅台 2023 年营业收入是多少？同比增长率？",
        "expected_docs": ["d001"],
    },
    {
        "id": "demo-analytical",
        "question": "宁德时代近期有哪些潜在经营风险？",
        "expected_docs": ["d002", "d003"],
    },
    {
        "id": "demo-reasoning",
        "question": "美联储加息对 A 股新能源板块可能产生什么影响？",
        "expected_docs": ["d003", "d004"],
    },
]


def _write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(BASE_DIR / "documents.json", DOCUMENTS)
    _write_json(BASE_DIR / "chunks.json", CHUNKS)
    _write_json(BASE_DIR / "demo_cases.json", DEMO_CASES)
    print(f"Wrote processed fixtures to {BASE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
