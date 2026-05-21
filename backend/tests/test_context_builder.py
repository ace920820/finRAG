from app.core.agent.context_builder import build_evidence_pack
from app.core.agent.prompts import build_generation_prompt
from app.models.events import IntentDetectedEvent
from app.models.schemas import RerankResultItem


def _item(**overrides):
    payload = {
        "chunk_id": "chunk-1",
        "rank": 1,
        "title": "NVIDIA Q3",
        "doc_type": "financial_report",
        "company": "NVIDIA",
        "date": "2025-11-19",
        "page": 21,
        "content": "content",
        "citation_id": 1,
        "metadata": {},
    }
    payload.update(overrides)
    return RerankResultItem(**payload)


def test_build_evidence_pack_preserves_table_fact_fields():
    item = _item(
        chunk_id="fact-nvda-q3-revenue",
        content="Table fact: Revenue = 57,006",
        metadata={
            "chunk_type": "table_fact",
            "metric": "revenue",
            "metric_label": "Total revenue",
            "raw_value": "57,006",
            "value": 57006,
            "unit": "USD millions",
            "currency": "USD",
            "period_label": "FY2026 Q3",
            "table_id": "tbl-income",
            "page_num": 21,
            "source_pdf_name": "NVDA_nvidia_10q_FY2026Q3_2025-11-19.pdf",
        },
    )

    pack = build_evidence_pack([item])

    assert pack.original_count == 1
    assert pack.compressed_count == 1
    packed = pack.items[0]
    assert packed.citation_id == 1
    assert packed.preserved_fields["raw_value"] == "57,006"
    assert packed.preserved_fields["value"] == 57006
    assert packed.preserved_fields["unit"] == "USD millions"
    assert packed.preserved_fields["currency"] == "USD"
    assert packed.preserved_fields["period_label"] == "FY2026 Q3"
    assert packed.preserved_fields["table_id"] == "tbl-income"
    assert packed.preserved_fields["page_num"] == 21
    assert packed.preserved_fields["source_pdf_name"].startswith("NVDA_nvidia")
    assert "57,006" in packed.compact_content


def test_build_evidence_pack_dedupes_duplicate_table_facts():
    metadata = {
        "chunk_type": "table_fact",
        "metric": "revenue",
        "raw_value": "57,006",
        "period_label": "FY2026 Q3",
        "table_id": "tbl-income",
        "source_pdf_name": "NVDA_nvidia_10q_FY2026Q3_2025-11-19.pdf",
    }
    first = _item(chunk_id="", citation_id=1, metadata=metadata)
    duplicate = _item(chunk_id="", citation_id=2, metadata=metadata)

    pack = build_evidence_pack([first, duplicate])

    assert pack.original_count == 2
    assert pack.compressed_count == 1
    assert pack.dropped_duplicate_count == 1
    assert pack.items[0].citation_id == 1


def test_build_evidence_pack_compacts_long_text_and_preserves_source_metadata():
    long_content = "风险因素 " * 300
    item = _item(
        chunk_id="risk-1",
        title="CATL research note",
        doc_type="research_report",
        company="宁德时代",
        date="2026-01-01",
        page=5,
        content=long_content,
        metadata={"source": "catl-risk.pdf", "section": "风险因素"},
    )

    pack = build_evidence_pack([item], text_limit=120)

    packed = pack.items[0]
    assert packed.citation_id == 1
    assert packed.source == "catl-risk.pdf"
    assert packed.section == "风险因素"
    assert len(packed.compact_content) <= 120
    assert packed.compact_content.endswith("...")


def test_build_evidence_pack_handles_empty_evidence():
    pack = build_evidence_pack([])

    assert pack.original_count == 0
    assert pack.compressed_count == 0
    assert pack.dropped_duplicate_count == 0
    assert pack.items == []


def test_build_evidence_pack_defaults_missing_citation_id():
    class MinimalItem:
        chunk_id = "chunk-without-citation"
        title = "Minimal"
        doc_type = "research_report"
        company = "NVIDIA"
        date = "2026-01-01"
        page = None
        content = "content"
        metadata = {}

    pack = build_evidence_pack([MinimalItem()])

    assert pack.items[0].citation_id == 0


def test_generation_prompt_uses_compact_evidence_content():
    long_content = "风险因素 " * 300
    item = _item(chunk_id="risk-2", content=long_content, metadata={"source": "risk.pdf"})
    pack = build_evidence_pack([item], text_limit=80)
    prompt = build_generation_prompt(
        "宁德时代风险",
        IntentDetectedEvent(intent="analytical", template="analytical_markdown_with_citations"),
        [item],
        evidence_pack=pack,
    )

    assert pack.items[0].compact_content in prompt
    assert long_content not in prompt
