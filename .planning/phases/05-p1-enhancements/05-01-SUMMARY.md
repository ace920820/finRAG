---
phase: 05-p1-enhancements
plan: 01
subsystem: preview-backend
tags: [api, preview, query-analysis]
key-files:
  - backend/app/api/preview_rewrite.py
  - backend/app/core/agent/query_analysis.py
  - backend/app/main.py
  - backend/tests/test_preview_rewrite.py
metrics:
  tests: 3 passed
---

# Plan 05-01 Summary: Preview Rewrite Backend

## Completed

- Added `POST /api/preview-rewrite` as a lightweight deterministic preview endpoint.
- Reused existing query analysis for expanded terms, sub-queries, and intent.
- Added deterministic entity detection for the demo companies and related financial terms.
- Added tests for the preview endpoint and entity detection.

## Deviations

- No new NER dependency was added; entity detection is alias-driven and intentionally small.

## Self-Check

PASSED — `cd backend && python3 -m pytest tests/test_preview_rewrite.py`.
