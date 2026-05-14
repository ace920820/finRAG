from app.core.ingestion.fixture_loader import load_documents


def test_kb_overview(client):
    response = client.get("/api/kb/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_documents"] >= 1
    assert payload["total_chunks"] >= 1
    assert payload["status"] == "ready"


def test_kb_documents_list_supports_search_and_pagination(client):
    all_response = client.get("/api/kb/documents?page=1&page_size=2")
    assert all_response.status_code == 200
    all_payload = all_response.json()
    assert all_payload["total"] >= 1
    assert len(all_payload["documents"]) <= 2

    first_title = all_payload["documents"][0]["title"]
    search_response = client.get("/api/kb/documents", params={"q": first_title[:4]})
    assert search_response.status_code == 200
    assert search_response.json()["total"] >= 1


def test_kb_document_detail(client):
    document = load_documents()[0]
    response = client.get(f"/api/kb/documents/{document.doc_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["doc_id"] == document.doc_id
    assert payload["chunk_count"] >= 1
    assert payload["status"] == "active"
    assert "chunks" in payload


def test_kb_document_detail_404(client):
    response = client.get("/api/kb/documents/missing")

    assert response.status_code == 404


def test_kb_overview_uses_expected_40_pdf_corpus(client):
    response = client.get('/api/kb/overview')

    assert response.status_code == 200
    payload = response.json()
    assert payload['total_documents'] == 40
    assert payload['total_chunks'] >= 9303
