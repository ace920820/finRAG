# Phase 4 Validation Checklist

**Created:** 2026-05-13

## Goal-Backward Validation

Phase 4 is complete only when the imported React frontend can run against the local FastAPI backend through `/api`, replace the timer/mock RAG flow with real backend SSE events, and preserve the existing UI state shape and visual layout.

## Required Evidence

- `frontend/vite.config.ts` proxies `/api` to the backend dev server.
- Frontend has an API adapter for `GET /api/documents` and `POST /api/query`.
- Frontend parses POST SSE frames and handles `query_rewrite`, `retrieval_complete`, `rerank_complete`, `answer_chunk`, `done`, `error`, and `ping`.
- `SidebarLeft` document library is populated from `GET /api/documents` through mapping into existing document label shape.
- `SidebarRight` receives backend BM25/vector/rerank arrays through existing props.
- `ChatArea` receives streamed Markdown answer chunks and clickable citation span markup.
- Three demo questions can be run through the UI with visible stage updates.
- Frontend TypeScript validation passes.
- Backend pytest suite still passes.

## Validation Commands

```bash
cd backend && python3 -m pytest
cd frontend && npm run lint
cd frontend && npm run build
```


## Automated Validation Record

Commands to run before Phase 4 completion:

```bash
cd backend && python3 -m pytest
cd frontend && npm run lint
cd frontend && npm run build
```

Implemented files covered by these checks:

- `frontend/src/api/finrag.ts` — backend schema mapping and POST SSE parser.
- `frontend/src/App.tsx` — backend-driven message, retrieval panel, and error state.
- `frontend/src/components/SidebarLeft.tsx` — backend-loaded document library props.
- `frontend/vite.config.ts` — `/api` proxy to local FastAPI backend.

## Manual Smoke Check

Run both services locally:

```bash
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Then test:

1. “贵州茅台 2023 年营业收入是多少？同比增长率？”
2. “宁德时代近期有哪些潜在经营风险？”
3. “美联储加息对 A 股新能源板块可能产生什么影响？”

Expected: stage updates progress, right retrieval panel updates, answer streams, citations are clickable, and reset clears active state.

## Out Of Scope Checks

- No frontend visual redesign.
- No new backend retrieval or generation features.
- No production deployment/authentication.
- No live provider credential requirement.
