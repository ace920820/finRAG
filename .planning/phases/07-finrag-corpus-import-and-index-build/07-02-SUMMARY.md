---
phase: 07-finrag-corpus-import-and-index-build
plan: 02
subsystem: import-index-integration
tags: [cli, index, api, retrieval]
key-files:
  - backend/scripts/import_corpus.py
  - backend/scripts/build_index.py
  - backend/app/core/retrieval/index_store.py
  - backend/tests/test_import_pipeline_integration.py
metrics:
  integration-tests: 2 passed
  focused-backend-tests: 11 passed
---

# Plan 07-02 Summary: Import CLI And Retrieval Integration

## Completed

- Added `backend/scripts/import_corpus.py` for raw corpus import with optional `--rebuild-index`.
- Extended `backend/scripts/build_index.py` with explicit `--processed-dir` and `--index-dir` support.
- Added force rebuild support to `RetrievalIndexStore.load_or_build()` so imported chunks do not reuse stale vectors.
- Added integration tests for CLI import, index artifact creation, loader/API visibility, and hybrid retrieval over imported content.

## Deviations

- Tests use temporary processed/index directories and mock embedding behavior; no Bailian credentials are required.

## Self-Check

PASSED — `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_import_pipeline_integration.py tests/test_retrieval_index.py tests/test_documents_api.py tests/test_hybrid_retrieval.py`.
