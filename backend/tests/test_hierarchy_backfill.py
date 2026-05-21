from app.models.schemas import Chunk
from scripts.backfill_hierarchy import backfill_chunks


def test_backfill_chunks_adds_text_parents_without_changing_existing_ids():
    chunks = [
        Chunk(
            chunk_id="doc-a-c0001",
            doc_id="doc-a",
            section="chunk-1",
            page_num=1,
            chunk_index=1,
            content="risk paragraph",
            metadata={"source": "report-a.pdf", "company": "A", "doc_type": "research_report", "date": "2026-01-01"},
        ),
        Chunk(
            chunk_id="doc-a-c0002",
            doc_id="doc-a",
            section="chunk-2",
            page_num=2,
            chunk_index=2,
            content="second paragraph",
            metadata={"source": "report-a.pdf", "company": "A", "doc_type": "research_report", "date": "2026-01-01"},
        ),
    ]

    updated, parents = backfill_chunks(chunks)

    assert [chunk.chunk_id for chunk in updated] == ["doc-a-c0001", "doc-a-c0002"]
    assert len(parents) == 1
    assert parents[0].metadata["chunk_level"] == "section"
    assert parents[0].metadata["child_ids"] == ["doc-a-c0001", "doc-a-c0002"]
    assert updated[0].metadata["parent_id"] == parents[0].chunk_id
    assert updated[0].metadata["section_path"] == ["report-a.pdf", "Pages 1-2"]


def test_backfill_chunks_links_existing_table_rows():
    table = Chunk(
        chunk_id="doc-a-t0001",
        doc_id="doc-a",
        section="table:income",
        page_num=5,
        chunk_index=3,
        content="table income",
        metadata={
            "chunk_type": "table",
            "table_id": "income",
            "table_title": "Income Statement",
            "source": "report-a.pdf",
            "company": "A",
            "doc_type": "financial_report",
            "date": "2026-01-01",
        },
    )
    row = Chunk(
        chunk_id="doc-a-tr0001",
        doc_id="doc-a",
        section="table:income:row:1",
        page_num=5,
        chunk_index=4,
        content="revenue row",
        metadata={
            "chunk_type": "table_row",
            "table_id": "income",
            "source": "report-a.pdf",
            "company": "A",
            "doc_type": "financial_report",
            "date": "2026-01-01",
        },
    )

    updated, parents = backfill_chunks([table, row])
    by_id = {chunk.chunk_id: chunk for chunk in updated}

    assert parents == []
    assert by_id["doc-a-t0001"].metadata["child_ids"] == ["doc-a-tr0001"]
    assert by_id["doc-a-tr0001"].metadata["parent_id"] == "doc-a-t0001"
    assert by_id["doc-a-tr0001"].metadata["section_path"] == ["tables", "Income Statement"]
