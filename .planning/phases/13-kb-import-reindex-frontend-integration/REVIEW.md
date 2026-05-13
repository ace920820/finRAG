# Phase 13+ Code Review

Scope: phase 13 implementation plus phase 14-16 planning artifacts.

## Findings

### High — Live embedding search still uses the mock model
- `backend/app/core/retrieval/vector_store.py:62-66` always embeds the query with `MockEmbeddingProvider`, even when the index was built with Bailian/OpenAI-compatible embeddings.
- Once `FINRAG_EMBEDDING_PROVIDER=bailian`, stored vectors and query vectors will have different dimensions, so live retrieval can fail or return meaningless scores.
- This breaks the main retrieval path for any non-mock deployment and is not covered by the current tests, which only exercise the mock provider.

### High — KB import API trusts arbitrary filesystem paths
- `backend/app/api/kb.py:146-158` accepts `source_dir` and `processed_dir` directly from the request and passes them into `import_corpus`.
- That lets a caller point the backend at arbitrary read/write locations on the server filesystem.
- For a demo service this is still risky; if the API is reachable beyond localhost, it becomes a straightforward path traversal / arbitrary file write issue.

### Medium — PDF upload is advertised but not actually imported
- `backend/app/api/kb.py:119-136` accepts `.pdf` uploads, but `backend/app/core/ingestion/raw_loader.py:18-32` only discovers `.md` and `.txt` files for import.
- The KB UI also exposes PDF as an allowed import type, so users can upload a PDF successfully and still get a failed or no-op import.
- This is a contract mismatch with `docs/知识库管理PRD.md:156-160`, which says the backend should receive PDF/Markdown/TXT.

### Medium — Reimport and soft-delete endpoints are non-persistent no-ops
- `backend/app/api/kb.py:198-218` returns success for `POST /api/kb/documents/{doc_id}/reimport` and `DELETE /api/kb/documents/{doc_id}` without changing `documents.json`, `chunks.json`, or any status store.
- `list_kb_documents()` and `get_kb_document()` always hardcode `status="active"`, so the UI will show a successful delete/reimport even though the corpus never changes.
- This breaks the management workflow promised in the PRD and the interface spec.

## Notes

- Phase 14-16 are planning-only artifacts in the current tree; I did not find runtime code defects there because there is no implementation yet.
