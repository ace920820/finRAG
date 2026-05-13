# Phase 8 Summary: Real-Corpus Entry Points

## Completed
- Rewrote the three left-sidebar examples around the imported corpus companies.
- Added clickable document library rows.
- Added `/api/documents/{doc_id}/view` for readable document opening.
- Extended document list payload with source metadata while preserving existing fields.

## Validation
- `cd frontend && npm run lint && npm run build` passed.
- `cd backend && python3 -m pytest tests/test_documents_api.py tests/test_query_api.py` passed.
