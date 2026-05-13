# Phase 10–12 Code Review

Review date: 2026-05-14
Scope: Phase 10 per-turn evidence traceability, Phase 11 single-app KB manager integration, Phase 12 KB backend API foundation.

## Summary

- Findings: 5 total
- High: 1
- Medium: 3
- Low: 1
- Note: Phase 12 plan describes read-only KB APIs, but current implementation also includes upload/import/reindex/delete/reimport paths. Those write paths are reviewed because they are now reachable from the frontend.

## Findings

### High — Rebuild Index button is not wired

- File: `frontend/src/pages/KnowledgeBaseManager.tsx:314`
- Impact: The UI displays a primary knowledge-base maintenance action, but clicking `重建索引` does nothing. `handleReindex()` exists and calls `/api/kb/reindex`, so this is a wiring bug rather than a missing backend feature.
- Evidence: `handleReindex` is defined at `frontend/src/pages/KnowledgeBaseManager.tsx:139`, while the button at `frontend/src/pages/KnowledgeBaseManager.tsx:314` has no `onClick` handler.
- Recommendation: Add `type="button"` and `onClick={() => void handleReindex()}`; optionally disable it while a reindex task is running.

### Medium — Upload silently overwrites existing files

- File: `backend/app/api/kb.py:134`
- Impact: Uploading another file with the same basename into the same collection overwrites the previous raw file without warning. This can corrupt the source corpus and make later imports non-reproducible.
- Evidence: The target path is computed directly as `target_dir / filename`, then opened with `"wb"` at `backend/app/api/kb.py:135`.
- Recommendation: Reject duplicate filenames with `409 Conflict`, or generate a unique server-side filename while preserving the original name in metadata.

### Medium — Upload API leaks absolute server paths

- File: `backend/app/api/kb.py:137`
- Impact: `/api/kb/upload` returns full local filesystem paths such as the configured data directory. This leaks deployment layout to any API caller and couples the frontend contract to server internals.
- Evidence: `saved_paths.append(str(target_path))` returns the absolute `Path` created under `get_settings().data_dir`.
- Recommendation: Return collection-relative paths, file IDs, or sanitized filenames; keep absolute paths server-side only.

### Medium — Disabled documents remain in the active RAG corpus

- File: `backend/app/api/kb.py:219`
- Impact: `DELETE /api/kb/documents/{doc_id}` marks a document disabled only in `kb_state.json`. It does not remove the document from `documents.json`, `chunks.json`, or the retrieval index, so the same document can still be returned by chat retrieval after being “deleted/disabled” in KB management.
- Evidence: `disable_document` only calls `_update_document_state` at `backend/app/api/kb.py:223`; retrieval APIs load processed chunks/documents independently from this state.
- Recommendation: Rename the action as UI-only archival if that is intended, or make retrieval/index building filter out disabled doc IDs and trigger/recommend reindex after disabling.

### Low — Document list repeatedly reloads all chunks

- File: `backend/app/api/kb.py:230`
- Impact: `GET /api/kb/documents` calls `_document_item()` per document, and `_document_item()` calls `load_chunks()` then scans chunks for that document. This creates avoidable O(document_count × chunk_count) work.
- Evidence: `list_kb_documents` maps every document through `_document_item` at `backend/app/api/kb.py:75`; `_document_item` loops over `load_chunks()` at `backend/app/api/kb.py:230`.
- Recommendation: Load chunks once in `list_kb_documents`, precompute `{doc_id: first_chunk_metadata}`, and pass that into `_document_item`.

## Non-Blocking Observations

- `frontend/src/components/ChatArea.tsx:159` converts every numeric Markdown pattern like `[2024]` into a citation chip. If the LLM emits bracketed years or list references that are not citations, they become clickable false citations. Consider only converting IDs present in `msg.retrievalSnapshot?.citations`.
- `frontend/src/pages/KnowledgeBaseManager.tsx:98` and `frontend/src/pages/KnowledgeBaseManager.tsx:99` still initialize with mock stats/docs. This matched Phase 11’s note, but after real API wiring it can mislead users during API failures because stale mock data remains visible beside the error.

## Suggested Verification

- Frontend: add a focused test or manual smoke test that clicks `重建索引` and sees a new reindex task.
- Backend: add API tests for duplicate upload behavior and for redacting absolute upload paths.
- Retrieval semantics: add a regression test proving disabled documents are excluded from chat retrieval, if disabled is meant to affect answers.
