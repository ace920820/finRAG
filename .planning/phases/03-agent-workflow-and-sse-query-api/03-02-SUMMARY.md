---
phase: 03-agent-workflow-and-sse-query-api
plan: 02
subsystem: query-sse-api
tags: [fastapi, sse, query-api, streaming]
key-files:
  - backend/app/api/query.py
  - backend/app/core/sse.py
  - backend/app/main.py
  - backend/tests/test_sse_formatter.py
  - backend/tests/test_query_api.py
metrics:
  tests: 5 passed
---

# Plan 03-02 Summary: SSE Query API

## Completed

- Added reusable SSE formatting helpers for JSON events, ping, error, and Markdown chunking.
- Added `POST /api/query` as a `text/event-stream` endpoint.
- Registered the query router in the FastAPI app factory.
- Streamed stable events: `query_rewrite`, `intent_detected`, `retrieval_complete`, `rerank_complete`, `ping`, `answer_chunk`, and `done`.
- Added SSE formatter and query endpoint tests.

## Deviations

- Heartbeat is emitted at a safe deterministic point instead of timed every 15 seconds, because automated tests should not be timing-sensitive and local mock generation is fast.

## Self-Check

PASSED — `cd backend && python3 -m pytest tests/test_sse_formatter.py tests/test_query_api.py`.
