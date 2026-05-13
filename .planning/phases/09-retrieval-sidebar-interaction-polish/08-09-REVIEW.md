# Phase 8–9 Code Review

Review date: 2026-05-14
Scope: Phase 8 real-corpus entry points and Phase 9 retrieval sidebar interaction polish.

## Summary

- Findings: 3 total
- High: 0
- Medium: 1
- Low: 2
- Review target: current working tree, focusing on files introduced or changed for Phase 8/9.

## Findings

### Medium — Rerank expansion state can leak between different result sets

- File: `frontend/src/components/SidebarRight.tsx:58`
- Impact: Rerank items are keyed as `${doc.id}-${index}`, while `doc.id` for rerank results is the citation number (`1`–`5`) from `frontend/src/api/finrag.ts:178`. Those keys repeat across queries and selected turns, so React can reuse the same `RerankItem` component and preserve its local `expanded` state for a different evidence chunk. A user may expand Top 1 for one query, then see Top 1 already expanded for another query even though it is different evidence.
- Evidence: `RerankItem` owns local expansion state at `frontend/src/components/SidebarRight.tsx:115`, but the parent key does not include a stable evidence identity such as `chunk_id`.
- Recommendation: Preserve `chunk_id` or another stable evidence key on the frontend `Document` model and key rerank items by that value plus snapshot/message identity; alternatively reset `expanded` when the evidence text/title changes.

### Low — Document open URL is client-derived instead of part of the API contract

- File: `frontend/src/api/finrag.ts:202`
- Impact: Phase 8 planned to extend document list item data with a document open URL, but `/api/documents` returns only source metadata and the frontend constructs `/api/documents/{doc_id}/view` locally. This works in the current same-origin Vite proxy setup, but couples the client to backend route shape and can break behind a path prefix, API gateway, or future route change.
- Evidence: `backend/app/models/schemas.py:33` defines `DocumentListItem` without an open/view URL field; `mapDocumentListItem` hard-codes the route at `frontend/src/api/finrag.ts:202`.
- Recommendation: Add an `open_url` or `view_url` field to `DocumentListItem` and map it directly in the frontend, keeping the route contract backend-owned.

### Low — Document view endpoint lacks direct regression coverage

- File: `backend/tests/test_documents_api.py:2`
- Impact: Phase 8 added `/api/documents/{doc_id}/view`, but the test file only covers `/api/documents`. Regressions in HTML rendering, escaping, or 404 behavior would not be caught by the current targeted tests listed in the Phase 8 summary.
- Evidence: `backend/app/api/documents.py:20` implements the view endpoint; `backend/tests/test_documents_api.py:2` only asserts list response shape.
- Recommendation: Add tests for a successful document view response containing escaped HTML and for a missing `doc_id` returning 404.

## Non-Blocking Observations

- `frontend/src/components/SidebarLeft.tsx:33` opens fallback mock documents with `openUrl: '#'` when document loading fails. This is acceptable for a demo fallback, but it may look like a broken document action during backend outages.
- `backend/app/api/documents.py:27` renders full document content into one HTML response. Current corpus sizes are manageable for local demo, but a future larger corpus may need chunked/paginated viewing.

## Suggested Verification

- Frontend: manually expand a rerank card, run a second query, and confirm expansion does not carry over to unrelated evidence.
- Backend: add `test_document_view_endpoint` and `test_document_view_404` to `backend/tests/test_documents_api.py`.
