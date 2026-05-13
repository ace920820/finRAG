import json
from pathlib import Path

from app.core.config import get_settings
from app.core.ingestion.fixture_loader import _processed_dir


def test_kb_upload_rejects_unsupported_file(client):
    response = client.post(
        "/api/kb/upload",
        data={"collection_name": "demo"},
        files=[("files", ("bad.exe", b"nope", "application/octet-stream"))],
    )

    assert response.status_code == 400


def test_kb_upload_import_and_job_polling(client, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    index_dir = data_dir / "index"
    monkeypatch.setenv("FINRAG_DATA_DIR", str(data_dir))
    monkeypatch.setenv("FINRAG_PROCESSED_DATA_DIR", str(processed_dir))
    monkeypatch.setenv("FINRAG_INDEX_DIR", str(index_dir))
    get_settings.cache_clear()
    _processed_dir.cache_clear()

    upload_response = client.post(
        "/api/kb/upload",
        data={"collection_name": "demo"},
        files=[("files", ("demo.md", b"# Demo Report\n\nhello world", "text/markdown"))],
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["uploaded"] == 1

    import_response = client.post(
        "/api/kb/import",
        json={"collection_name": "demo", "rebuild_index": False, "default_company": "DemoCo"},
    )
    assert import_response.status_code == 200
    job = import_response.json()
    assert job["status"] == "completed"
    assert job["success_count"] == 1

    poll_response = client.get(f"/api/kb/import-jobs/{job['job_id']}")
    assert poll_response.status_code == 200
    assert poll_response.json()["job_id"] == job["job_id"]

    documents = json.loads((processed_dir / "documents.json").read_text(encoding="utf-8"))
    assert documents[0]["company"] == "DemoCo"

    get_settings.cache_clear()
    _processed_dir.cache_clear()


def test_kb_reindex(client, tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    index_dir = tmp_path / "index"
    processed_dir.mkdir(parents=True)
    (processed_dir / "documents.json").write_text(
        json.dumps([
            {
                "doc_id": "doc-test",
                "company": "DemoCo",
                "company_aliases": [],
                "doc_type": "research_report",
                "title": "Demo",
                "date": "2026-05-13",
                "source": "demo.md",
                "content": "hello world",
            }
        ]),
        encoding="utf-8",
    )
    (processed_dir / "chunks.json").write_text(
        json.dumps([
            {
                "chunk_id": "chunk-test",
                "doc_id": "doc-test",
                "section": "Demo",
                "page_num": None,
                "chunk_index": 0,
                "content": "hello world",
                "metadata": {},
            }
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("FINRAG_PROCESSED_DATA_DIR", str(processed_dir))
    monkeypatch.setenv("FINRAG_INDEX_DIR", str(index_dir))
    get_settings.cache_clear()
    _processed_dir.cache_clear()

    response = client.post("/api/kb/reindex")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert (index_dir / "bm25_index.json").exists()
    assert (index_dir / "vector_index.json").exists()

    get_settings.cache_clear()
    _processed_dir.cache_clear()


def test_pdf_only_import_does_not_clear_existing_corpus(client, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    existing_documents = [
        {
            "doc_id": "doc-existing",
            "company": "ExistingCo",
            "company_aliases": [],
            "doc_type": "research_report",
            "title": "Existing Report",
            "date": "2026-05-13",
            "source": "existing.md",
            "content": "existing content",
        }
    ]
    existing_chunks = [
        {
            "chunk_id": "chunk-existing",
            "doc_id": "doc-existing",
            "section": "Existing",
            "page_num": None,
            "chunk_index": 0,
            "content": "existing content",
            "metadata": {},
        }
    ]
    (processed_dir / "documents.json").write_text(json.dumps(existing_documents), encoding="utf-8")
    (processed_dir / "chunks.json").write_text(json.dumps(existing_chunks), encoding="utf-8")
    monkeypatch.setenv("FINRAG_DATA_DIR", str(data_dir))
    monkeypatch.setenv("FINRAG_PROCESSED_DATA_DIR", str(processed_dir))
    get_settings.cache_clear()
    _processed_dir.cache_clear()

    upload_response = client.post(
        "/api/kb/upload",
        data={"collection_name": "pdf-only"},
        files=[("files", ("demo.pdf", b"%PDF-1.4\n", "application/pdf"))],
    )
    assert upload_response.status_code == 200

    import_response = client.post("/api/kb/import", json={"collection_name": "pdf-only"})

    assert import_response.status_code == 200
    assert import_response.json()["status"] == "failed"
    assert json.loads((processed_dir / "documents.json").read_text(encoding="utf-8")) == existing_documents
    assert json.loads((processed_dir / "chunks.json").read_text(encoding="utf-8")) == existing_chunks

    get_settings.cache_clear()
    _processed_dir.cache_clear()


def test_markdown_import_merges_with_existing_corpus(client, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    existing_documents = [
        {
            "doc_id": "doc-existing",
            "company": "ExistingCo",
            "company_aliases": [],
            "doc_type": "research_report",
            "title": "Existing Report",
            "date": "2026-05-13",
            "source": "existing.md",
            "content": "existing content",
        }
    ]
    existing_chunks = [
        {
            "chunk_id": "chunk-existing",
            "doc_id": "doc-existing",
            "section": "Existing",
            "page_num": None,
            "chunk_index": 0,
            "content": "existing content",
            "metadata": {},
        }
    ]
    (processed_dir / "documents.json").write_text(json.dumps(existing_documents), encoding="utf-8")
    (processed_dir / "chunks.json").write_text(json.dumps(existing_chunks), encoding="utf-8")
    monkeypatch.setenv("FINRAG_DATA_DIR", str(data_dir))
    monkeypatch.setenv("FINRAG_PROCESSED_DATA_DIR", str(processed_dir))
    get_settings.cache_clear()
    _processed_dir.cache_clear()

    upload_response = client.post(
        "/api/kb/upload",
        data={"collection_name": "new-md"},
        files=[("files", ("new.md", b"# New Report\n\nnew content", "text/markdown"))],
    )
    assert upload_response.status_code == 200

    import_response = client.post("/api/kb/import", json={"collection_name": "new-md", "default_company": "NewCo"})

    assert import_response.status_code == 200
    assert import_response.json()["status"] == "completed"
    documents = json.loads((processed_dir / "documents.json").read_text(encoding="utf-8"))
    assert {item["company"] for item in documents} == {"ExistingCo", "NewCo"}
    chunks = json.loads((processed_dir / "chunks.json").read_text(encoding="utf-8"))
    assert any(item["chunk_id"] == "chunk-existing" for item in chunks)

    get_settings.cache_clear()
    _processed_dir.cache_clear()
