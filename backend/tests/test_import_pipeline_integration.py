from __future__ import annotations

import json
import subprocess

from app.core.config import get_settings
from app.core.ingestion.fixture_loader import _processed_dir, chunk_counts_by_doc_id, load_documents
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.index_store import RetrievalIndexStore


def _write_sample_raw(raw_root):
    source = raw_root / "extracted" / "reports"
    source.mkdir(parents=True)
    (source / "贵州茅台-渠道跟踪.md").write_text(
        "\n".join([
            "---",
            'collection: "reports"',
            'title: "贵州茅台 渠道跟踪"',
            'source_pdf_name: "贵州茅台 渠道跟踪.pdf"',
            'company: "贵州茅台"',
            'company_aliases: "茅台,600519"',
            'doc_type: "research_report"',
            'date: "2026-05-01"',
            'content_hash: "moutai-channel"',
            "---",
            "",
            "## Extracted Text",
            "",
            "<!-- page: 2 -->",
            "贵州茅台渠道库存稳定，批价表现稳健，营业收入具备韧性。",
        ]),
        encoding="utf-8",
    )


def test_import_cli_builds_processed_json_and_rebuilds_indexes(tmp_path):
    raw_root = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    index_dir = tmp_path / "index"
    _write_sample_raw(raw_root)

    completed = subprocess.run(
        [
            "python3",
            "scripts/import_corpus.py",
            "--raw-root",
            str(raw_root),
            "--collection-name",
            "reports",
            "--processed-dir",
            str(processed_dir),
            "--index-dir",
            str(index_dir),
            "--rebuild-index",
        ],
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Corpus import finished." in completed.stdout
    documents = json.loads((processed_dir / "documents.json").read_text(encoding="utf-8"))
    chunks = json.loads((processed_dir / "chunks.json").read_text(encoding="utf-8"))
    assert documents[0]["title"] == "贵州茅台 渠道跟踪"
    assert chunks[0]["metadata"]["source_pdf_name"] == "贵州茅台 渠道跟踪.pdf"
    assert (index_dir / "bm25_index.json").exists()
    assert (index_dir / "vector_index.json").exists()


def test_imported_corpus_flows_through_loader_api_and_retrieval(tmp_path, client):
    raw_root = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    index_dir = tmp_path / "index"
    _write_sample_raw(raw_root)

    subprocess.run(
        [
            "python3",
            "scripts/import_corpus.py",
            "--raw-root",
            str(raw_root),
            "--collection-name",
            "reports",
            "--processed-dir",
            str(processed_dir),
        ],
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
        check=True,
    )

    settings = get_settings()
    old_processed_dir = settings.processed_data_dir
    old_index_dir = settings.index_dir
    settings.processed_data_dir = processed_dir
    settings.index_dir = index_dir
    _processed_dir.cache_clear()
    try:
        documents = load_documents()
        assert documents[0].title == "贵州茅台 渠道跟踪"
        counts = chunk_counts_by_doc_id()
        assert counts[documents[0].doc_id] == 1

        response = client.get("/api/documents")
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["documents"][0]["company"] == "贵州茅台"

        index_dir.mkdir(parents=True, exist_ok=True)
        for stale_index in index_dir.glob("*.json"):
            stale_index.unlink()
        index_store = RetrievalIndexStore.load_or_build(force_rebuild=True)
        retriever = HybridRetriever(index_store.bm25_store, index_store.vector_store)
        results = retriever.retrieve("贵州茅台 渠道库存 营业收入", top_k=5)
        assert any("渠道库存" in item.preview for item in results.fused_top20)
        index_store.save()
        assert (index_dir / "bm25_index.json").exists()
        assert (index_dir / "vector_index.json").exists()
    finally:
        settings.processed_data_dir = old_processed_dir
        settings.index_dir = old_index_dir
        _processed_dir.cache_clear()
