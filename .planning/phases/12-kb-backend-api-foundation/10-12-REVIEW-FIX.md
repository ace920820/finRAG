# Phase 10–12 Review Fix Summary

Fix date: 2026-05-14
Source review: `.planning/phases/12-kb-backend-api-foundation/10-12-REVIEW.md`

## Fixed

- Wired the Knowledge Base Manager `重建索引` button to the existing `handleReindex` flow.
- Limited chat citation chip rendering to IDs present in the message retrieval snapshot, avoiding false citations like `[2024]`.
- Changed upload behavior to reject duplicate filenames with `409 Conflict` instead of overwriting raw files.
- Redacted upload responses to return data-dir-relative paths instead of absolute server paths.
- Added disabled-document filtering to index rebuilds through `load_active_chunks()`.
- Rebuilt retrieval indexes automatically when documents are disabled or reactivated via reimport.
- Avoided repeated chunk scans in the KB document list by precomputing first chunk metadata once.

## Tests

- `cd backend && python3 -m pytest tests/test_kb_import_api.py tests/test_kb_api.py`
- `cd frontend && npm run lint && npm run build`

## Notes

- Backend tests pass with existing PyMuPDF/SWIG deprecation warnings.
- Frontend build passes with the existing Vite chunk-size warning.
