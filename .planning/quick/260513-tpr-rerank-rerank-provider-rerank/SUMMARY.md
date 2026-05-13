# Quick Task 260513-tpr Summary

## Root Cause
Rerank degraded because the DashScope text-rerank endpoint expects request fields under `input.query` and `input.documents`. The provider was sending qwen3-rerank requests with top-level `query` and `documents`, causing HTTP 400.

## Fix
- Removed the qwen3-rerank top-level payload special case.
- The Bailian rerank provider now sends DashScope payload shape:
  - `model`
  - `input.query`
  - `input.documents`
  - `parameters.top_n`
- Updated provider tests to assert the DashScope payload shape.

## Validation
- Live direct API probe returned HTTP 200 and relevance scores.
- Live `/api/debug/retrieval` returned `degraded: False` with score source `rerank` and relevance scores around `0.72-0.82`.
- `cd backend && python3 -m pytest tests/test_provider_config.py tests/test_rerank_service.py tests/test_debug_retrieval.py tests/test_query_api.py` → 11 passed.
- `cd frontend && npm run lint` passed.
