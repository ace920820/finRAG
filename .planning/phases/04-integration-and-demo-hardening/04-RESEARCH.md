# Phase 4 Research: Integration And Demo Hardening

**Created:** 2026-05-13  
**Status:** Ready for planning

## Research Goal

Determine the smallest safe set of frontend and backend-adjacent changes needed to connect the imported React frontend to the completed FastAPI contracts, preserve the current UI, and validate the three demo questions end-to-end.

## Inputs Reviewed

- `.planning/ROADMAP.md` — Phase 4 goal and success criteria.
- `.planning/REQUIREMENTS.md` — `INTG-01` through `INTG-08`.
- `.planning/frontend-integration-readiness.md` — canonical frontend/backend mapping.
- `.planning/phases/04-integration-and-demo-hardening/04-CONTEXT.md` — Phase 4 decisions.
- `.planning/phases/03-agent-workflow-and-sse-query-api/03-VERIFICATION.md` — backend SSE contract verification.
- `backend/app/api/query.py` — backend query SSE endpoint.
- `backend/app/models/events.py` and `backend/app/models/schemas.py` — backend payload shapes.
- `frontend/src/App.tsx` — current timer/mock flow.
- `frontend/src/types.ts` — UI-facing state shapes.
- `frontend/src/components/SidebarLeft.tsx`, `SidebarRight.tsx`, `ChatArea.tsx` — existing UI boundaries.
- `frontend/src/data/mock.ts` — fallback shape examples.
- `frontend/vite.config.ts` and `frontend/package.json` — dev proxy/build/lint setup.

## Current Integration Gap

The backend now has the required contracts, but the frontend still simulates RAG locally:

- `App.tsx` uses `simulateRAGFlow()` with `setTimeout`/`setInterval`.
- `SidebarLeft` imports `mockLeftDocuments` directly.
- `SidebarRight` receives mock BM25/vector/rerank arrays from `mock.ts`.
- No `/api` proxy is configured in Vite.
- No frontend API adapter exists for `GET /api/documents` or `POST /api/query` SSE.

## Recommended Technical Approach

### 1. Add Frontend API Adapter Layer

Create a small adapter module, e.g. `frontend/src/api/finrag.ts`, with:

- Backend response types for documents, retrieval results, rerank results, SSE events, and citations.
- `fetchDocuments()` for `GET /api/documents`.
- `streamQuery(query, handlers)` for `POST /api/query`.
- Mapper functions that convert backend English schemas into UI `Document` and `Message` state fields.

Why: keeps backend naming differences away from UI components and makes Phase 4 integration testable without changing visual components.

### 2. Parse Fetch-Based SSE

Because `POST /api/query` uses SSE-like `text/event-stream`, `EventSource` is not suitable because it only supports GET. Use `fetch()` with `ReadableStream` and parse frames split by blank lines:

```ts
const response = await fetch('/api/query', { method: 'POST', body: JSON.stringify({ query }) })
const reader = response.body?.getReader()
```

Parser requirements:

- Accumulate partial chunks.
- Split on `\n\n` frame boundaries.
- Parse `event:` and `data:` lines.
- Call event handlers for known events.
- Treat `error` SSE events as recoverable UI errors.

### 3. Preserve Existing UI State

Minimal state changes in `App.tsx`:

- Keep `messages` and `activeCitationId`.
- Add `bm25Docs`, `vectorDocs`, `rerankDocs`, and `leftDocuments` state arrays.
- Replace `simulateRAGFlow` with an async `runRAGFlow` that updates the same message stages.
- Map event stages:
  - `query_rewrite` → assistant `stage: 'query'`, `queryRewrite` populated.
  - `retrieval_complete` → assistant `stage: 'retrieve'`, right panel BM25/vector updated.
  - `rerank_complete` → assistant `stage: 'rerank'`, right panel rerank updated.
  - first `answer_chunk` → assistant `stage: 'generate'`, append content.
  - `done` → assistant `stage: 'done'`, `tokens` populated.
  - `error` → assistant content updated with user-facing error, `stage: 'done'`.

### 4. SidebarLeft Prop Conversion

Change `SidebarLeft` to accept a document list prop while preserving markup:

```ts
interface SidebarLeftProps {
  documents: Array<{ id: string; title: string; type: DocType }>;
  onSelectExample: (text: string) => void;
}
```

Fallback to mock documents only if backend load fails or no documents are loaded yet.

### 5. Vite Proxy

Update `frontend/vite.config.ts` to proxy `/api` to `http://localhost:8000` in development. Keep the backend port aligned with FastAPI default Uvicorn usage.

### 6. Validation Strategy

Backend remains validated by pytest. Phase 4 should add frontend validation:

- `cd frontend && npm run lint` for TypeScript correctness.
- `cd frontend && npm run build` for production build integrity.
- Optional manual smoke:
  1. `cd backend && uvicorn app.main:app --reload`
  2. `cd frontend && npm run dev`
  3. Run each demo question through the UI.

Add a Phase 4 manual UAT/checklist doc because browser interaction cannot be fully validated through current automated backend tests.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| POST SSE parsing is fragile | Add a dedicated parser function and test it with sample Phase 3 frames. |
| UI redesign creep | Keep existing components, props, and CSS; adapter-only changes. |
| Backend unavailable during frontend demo | Show clear assistant error and optionally keep mock fallback for document list. |
| Citation spans break ReactMarkdown | Existing `ChatArea` uses raw HTML/citation parsing; preserve Phase 3 span format. |
| TypeScript types drift from backend | Define minimal backend payload types in adapter and test mapper functions. |

## Recommendation

Plan Phase 4 as three execution plans:

1. **Frontend API adapters and proxy** — add typed client, SSE parser, backend-to-UI mappers, Vite proxy.
2. **Wire imported React UI** — replace mock RAG flow and mock document library with backend data while preserving UI components.
3. **Demo hardening and validation** — add focused mapper/parser tests or TypeScript checks, manual UAT checklist, and run backend/frontend validation commands.

This sequencing isolates risky parsing/mapping before touching `App.tsx`, then validates the integrated demo path without redesigning frontend UI.
