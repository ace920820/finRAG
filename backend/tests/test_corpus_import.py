from __future__ import annotations

import json

import pytest

from app.core.ingestion.chunker import chunk_text
from app.core.ingestion.corpus_importer import ImportDefaults, import_corpus
from app.core.ingestion.raw_loader import discover_raw_inputs, parse_raw_document
from app.models.schemas import Chunk, Document


def test_parse_phase6_markdown_frontmatter_and_extracted_text(tmp_path):
    path = tmp_path / "贵州茅台-2025-年报.md"
    path.write_text(
        "\n".join([
            "---",
            'domain: "finrag"',
            'collection: "reports"',
            'title: "贵州茅台 2025 年报"',
            'source_pdf_name: "贵州茅台 2025 年报.pdf"',
            'source_pdf_path: "/source/贵州茅台 2025 年报.pdf"',
            'company: "贵州茅台"',
            'doc_type: "financial_report"',
            'date: "2026-03-28"',
            'content_hash: "abc123"',
            "---",
            "",
            "# 贵州茅台 2025 年报",
            "",
            "## Metadata",
            "",
            "ignored metadata block",
            "",
            "## Extracted Text",
            "",
            "<!-- page: 1 -->",
            "营业收入稳定增长。",
        ]),
        encoding="utf-8",
    )

    raw = parse_raw_document(path)

    assert raw.collection_name == "reports"
    assert raw.title == "贵州茅台 2025 年报"
    assert raw.source_name == "贵州茅台 2025 年报.pdf"
    assert raw.frontmatter["company"] == "贵州茅台"
    assert raw.body.startswith("<!-- page: 1 -->")
    assert "ignored metadata block" not in raw.body


def test_discover_raw_inputs_supports_extracted_and_manual_text(tmp_path):
    raw_root = tmp_path / "raw"
    extracted = raw_root / "extracted" / "reports"
    manual = raw_root / "manual" / "reports"
    extracted.mkdir(parents=True)
    manual.mkdir(parents=True)
    (extracted / "a.md").write_text("正文", encoding="utf-8")
    (manual / "b.txt").write_text("补充新闻", encoding="utf-8")
    (manual / "._junk.md").write_text("junk", encoding="utf-8")

    paths = discover_raw_inputs(raw_root, collection_name="reports")

    assert [path.name for path in paths] == ["a.md", "b.txt"]


def test_discover_raw_inputs_rejects_unsafe_collection_name(tmp_path):
    with pytest.raises(ValueError, match="collection_name"):
        discover_raw_inputs(tmp_path / "raw", collection_name="../outside")



def test_discover_raw_inputs_excludes_meta_manifests(tmp_path):
    raw_root = tmp_path / "raw"
    extracted = raw_root / "extracted" / "reports"
    meta = raw_root / "_meta"
    extracted.mkdir(parents=True)
    meta.mkdir(parents=True)
    (extracted / "report.md").write_text("正文", encoding="utf-8")
    (meta / "reports-extraction-manifest.md").write_text("# Manifest", encoding="utf-8")

    paths = discover_raw_inputs(raw_root)

    assert [path.name for path in paths] == ["report.md"]


def test_chunk_text_preserves_page_markers_and_order():
    chunks = chunk_text("<!-- page: 1 -->\n第一段。\n\n第二段。\n\n<!-- page: 2 -->\n第三段。", target_chars=20)

    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert [chunk.page_num for chunk in chunks] == [1, 2]
    assert chunks[0].content == "第一段。\n\n第二段。"
    assert chunks[1].section == "chunk-2"


def test_import_corpus_writes_schema_compatible_deterministic_json(tmp_path):
    raw_root = tmp_path / "raw"
    source = raw_root / "extracted" / "reports"
    source.mkdir(parents=True)
    markdown = source / "CATL quarterly.md"
    markdown.write_text(
        "\n".join([
            "---",
            'collection: "reports"',
            'title: "宁德时代 季度经营更新"',
            'source_pdf_name: "CATL quarterly.pdf"',
            'company: "宁德时代"',
            'company_aliases: "CATL,300750"',
            'doc_type: "research_report"',
            'date: "2026-04-01"',
            'content_hash: "stable-hash"',
            "---",
            "",
            "## Extracted Text",
            "",
            "# 经营概览",
            "",
            "<!-- page: 3 -->",
            "宁德时代动力电池出货增长，经营风险包括原材料价格波动。",
            "",
            "## 财务表现",
            "",
            "营业收入和盈利能力保持韧性。",
        ]),
        encoding="utf-8",
    )
    (source / "manual.txt").write_text("贵州茅台渠道库存保持稳定。", encoding="utf-8")
    processed_dir = tmp_path / "processed"

    first = import_corpus(
        raw_root=raw_root,
        processed_dir=processed_dir,
        collection_name="reports",
        defaults=ImportDefaults(company="默认公司", date="2026-01-01"),
        target_chars=50,
    )
    first_docs_json = first.documents_path.read_text(encoding="utf-8")
    first_chunks_json = first.chunks_path.read_text(encoding="utf-8")
    second = import_corpus(
        raw_root=raw_root,
        processed_dir=processed_dir,
        collection_name="reports",
        defaults=ImportDefaults(company="默认公司", date="2026-01-01"),
        target_chars=50,
    )

    documents = json.loads(first.documents_path.read_text(encoding="utf-8"))
    chunks = json.loads(first.chunks_path.read_text(encoding="utf-8"))

    assert len(first.documents) == 2
    assert len(first.chunks) == 4
    assert first_docs_json == second.documents_path.read_text(encoding="utf-8")
    assert first_chunks_json == second.chunks_path.read_text(encoding="utf-8")
    assert json.loads(first.facts_path.read_text(encoding="utf-8")) == []
    assert [Document(**item) for item in documents]
    assert [Chunk(**item) for item in chunks]
    catl = next(doc for doc in first.documents if doc.title == "宁德时代 季度经营更新")
    assert catl.company == "宁德时代"
    assert catl.company_aliases == ["CATL", "300750"]
    assert catl.date == "2026-04-01"
    catl_chunk = next(chunk for chunk in first.chunks if chunk.doc_id == catl.doc_id)
    assert catl_chunk.page_num == 3
    assert catl_chunk.metadata["source_pdf_name"] == "CATL quarterly.pdf"
    section_chunks = [chunk for chunk in first.chunks if chunk.doc_id == catl.doc_id and chunk.metadata.get("chunk_type") == "section"]
    assert [chunk.metadata["section_title"] for chunk in section_chunks] == ["财务表现"]
    finance_parent = section_chunks[0]
    overview_children = [
        chunk for chunk in first.chunks
        if chunk.metadata.get("parent_id") == finance_parent.chunk_id
    ]
    assert finance_parent.metadata["chunk_level"] == "section"
    assert finance_parent.metadata["section_path"] == ["经营概览", "财务表现"]
    assert finance_parent.metadata["child_ids"] == [child.chunk_id for child in overview_children]
    assert "宁德时代动力电池出货增长" in finance_parent.content
    assert overview_children[0].metadata["chunk_type"] == "text"
    assert overview_children[0].metadata["chunk_level"] == "paragraph"
    assert overview_children[0].metadata["section_title"] == "财务表现"
    assert overview_children[0].metadata["section_path"] == ["经营概览", "财务表现"]
    assert overview_children[0].metadata["hierarchy_path"] == ["经营概览", "财务表现", overview_children[0].section]
    manual_doc = next(doc for doc in first.documents if doc.title == "manual")
    assert manual_doc.company == "默认公司"
    assert manual_doc.doc_type == "research_report"


def test_import_corpus_infers_company_doc_type_and_date_from_pdf_path(tmp_path):
    raw_root = tmp_path / "raw"
    source = raw_root / "extracted" / "reports"
    source.mkdir(parents=True)
    markdown = source / "NVDA_nvidia_10k_FY2026_2026-02-25_q4cdn.md"
    markdown.write_text(
        "\n".join([
            "---",
            'source_pdf_name: "NVDA_nvidia_10k_FY2026_2026-02-25_q4cdn.pdf"',
            'source_pdf_path: "/source/nvidia/financial_reports/NVDA_nvidia_10k_FY2026_2026-02-25_q4cdn.pdf"',
            'content_hash: "nvda-2026"',
            "---",
            "",
            "## Extracted Text",
            "",
            "NVIDIA data center revenue increased.",
        ]),
        encoding="utf-8",
    )

    result = import_corpus(raw_root=raw_root, processed_dir=tmp_path / "processed", collection_name="reports")

    document = result.documents[0]
    assert document.company == "NVIDIA"
    assert document.company_aliases == ["NVDA"]
    assert document.doc_type == "financial_report"
    assert document.date == "2026-02-25"

def test_import_corpus_rejects_empty_inputs_without_overwriting_existing_processed_files(tmp_path):
    raw_root = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    documents_path = processed_dir / "documents.json"
    chunks_path = processed_dir / "chunks.json"
    documents_path.write_text('[{"doc_id":"existing"}]', encoding="utf-8")
    chunks_path.write_text('[{"chunk_id":"existing-c1"}]', encoding="utf-8")

    with pytest.raises(ValueError, match="No raw input documents"):
        import_corpus(raw_root=raw_root, processed_dir=processed_dir, collection_name="missing")

    assert documents_path.read_text(encoding="utf-8") == '[{"doc_id":"existing"}]'
    assert chunks_path.read_text(encoding="utf-8") == '[{"chunk_id":"existing-c1"}]'



def test_import_corpus_adds_structured_markdown_table_chunks(tmp_path):
    raw_root = tmp_path / "raw"
    source = raw_root / "extracted" / "reports"
    source.mkdir(parents=True)
    table_dir = raw_root / "tables" / "reports" / "NVDA-report"
    table_dir.mkdir(parents=True)
    markdown = source / "NVDA report.md"
    table_json = table_dir / "tbl-demo-p0001-t01.json"
    table_csv = table_dir / "tbl-demo-p0001-t01.csv"
    markdown.write_text(
        "\n".join([
            "---",
            'collection: "reports"',
            'title: "NVDA report"',
            'source_pdf_name: "NVDA report.pdf"',
            f'table_artifact_dir: "{table_dir}"',
            'company: "NVIDIA"',
            'doc_type: "financial_report"',
            'content_hash: "stable-table-hash"',
            "---",
            "",
            "## Extracted Text",
            "",
            "Plain text layer still exists.",
        ]),
        encoding="utf-8",
    )
    (table_dir / "._tbl-demo-p0001-t01.json").write_bytes(b"\x00\xb0not-json")
    table_json.write_text(json.dumps({
        "table_id": "tbl-demo-p0001-t01",
        "title": "Condensed Consolidated Statements of Income",
        "page_num": 7,
        "headers": ["Metric", "Oct 26 2025", "Oct 27 2024"],
        "rows": [["Revenue", "57,006", "35,082"], ["Cost of revenue", "15,157", "8,926"]],
        "markdown": "| Metric | Oct 26 2025 | Oct 27 2024 |\n| --- | --- | --- |\n| Revenue | 57,006 | 35,082 |\n| Cost of revenue | 15,157 | 8,926 |",
        "row_count": 2,
        "column_count": 3,
        "extraction_method": "pdfplumber",
        "csv_path": str(table_csv),
    }), encoding="utf-8")

    result = import_corpus(raw_root=raw_root, processed_dir=tmp_path / "processed", collection_name="reports")

    table_chunks = [chunk for chunk in result.chunks if chunk.metadata.get("chunk_type") == "table"]
    assert len(table_chunks) == 1
    chunk = table_chunks[0]
    assert chunk.section == "table:tbl-demo-p0001-t01"
    assert chunk.page_num == 7
    assert "| Revenue | 57,006 | 35,082 |" in chunk.content
    assert chunk.metadata["table_id"] == "tbl-demo-p0001-t01"
    assert chunk.metadata["row_count"] == 2
    assert chunk.metadata["chunk_level"] == "table"
    assert chunk.metadata["section_title"] == "Condensed Consolidated Statements of Income"
    assert chunk.metadata["section_path"] == ["tables", "Condensed Consolidated Statements of Income"]

    row_chunks = [chunk for chunk in result.chunks if chunk.metadata.get("chunk_type") == "table_row"]
    assert len(row_chunks) == 1
    assert row_chunks[0].metadata["metric"] == "revenue"
    assert row_chunks[0].metadata["chunk_level"] == "table_row"
    assert row_chunks[0].metadata["parent_id"] == chunk.chunk_id
    assert row_chunks[0].metadata["section_path"] == ["tables", "Condensed Consolidated Statements of Income"]
    assert chunk.metadata["child_ids"] == [row_chunks[0].chunk_id]
    assert "Table Row Metric: revenue" in row_chunks[0].content

    facts = json.loads(result.facts_path.read_text(encoding="utf-8"))
    assert [fact["value"] for fact in facts] == [57006, 35082]
    assert all(fact["metric"] == "revenue" for fact in facts)
    assert facts[0]["currency"] == "USD"
    assert facts[0]["unit"] == "USD millions"
    assert result.facts == facts
