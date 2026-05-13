# Phase 3 Validation Checklist

**Created:** 2026-05-13

## Goal-Backward Validation

Phase 3 is complete only when the backend can accept a financial research query through `POST /api/query` and stream a deterministic, source-grounded SSE sequence that the imported frontend can adapt to in Phase 4.

## Required Evidence

- `POST /api/query` exists and accepts `QueryRequest`.
- SSE events include `query_rewrite`, `intent_detected`, `retrieval_complete`, `rerank_complete`, `answer_chunk`, and `done` in a stable order.
- `retrieval_complete` includes `bm25_results`, `vector_results`, and `fused_top20`.
- `rerank_complete` includes top-5 results with `citation_id`.
- Answer chunks contain Markdown and citation markers compatible with frontend clickable citations.
- `done.citations` is keyed by citation ID and includes source metadata.
- Error/degraded paths are deterministic and do not require live API keys.
- Backend tests pass offline with mock providers.

## Validation Commands

```bash
cd backend && python3 -m pytest tests/test_query_analysis.py tests/test_sse_formatter.py tests/test_query_api.py
cd backend && python3 -m pytest
```

## Manual Smoke Check

If the backend is running locally, this command should stream the Phase 3 SSE contract:

```bash
curl -N -X POST http://localhost:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"宁德时代近期有哪些潜在经营风险？"}'
```

Look for `query_rewrite`, `intent_detected`, `retrieval_complete`, `rerank_complete`, `ping`, `answer_chunk`, and `done` in the response.

## Out Of Scope Checks

- No frontend redesign.
- No full multi-turn memory.
- No new retrieval algorithms.
- No live API smoke test requirement unless API credentials are explicitly provided later.
