# Frontend Integration Readiness

**Created:** 2026-05-13  
**Purpose:** Capture the imported React frontend's current mock contract and the backend/frontend integration preparation needed before Phase 4.

## Current Frontend State

The imported frontend under `frontend/` is a React/Vite app that currently simulates the RAG flow locally.

### Key Observations

- `frontend/src/App.tsx` drives the UI through `simulateRAGFlow()` with timers and mock data.
- `frontend/src/data/mock.ts` provides mock BM25, vector, rerank docs, answer stream, and rewrite keywords.
- `frontend/src/components/SidebarLeft.tsx` uses mock document metadata rather than `GET /api/documents`.
- `frontend/src/components/SidebarRight.tsx` expects three separate document arrays: BM25, vector, and rerank.
- `frontend/src/components/ChatArea.tsx` renders stage state from `Message.stage` and parses clickable citations from `<span class="cite" data-id="N">` style markup.
- `frontend/vite.config.ts` does not yet proxy `/api` to the backend.

## Frontend Model Shape

Frontend `Document` type:

```ts
interface Document {
  id: string;
  title: string;
  type: '财报' | '研报' | '新闻';
  source: string;
  score: number;
  contentSnippet?: string;
  isHigh?: boolean;
}
```

Backend currently uses English API values (`financial_report`, `research_report`, `news`) and backend response fields such as `chunk_id`, `doc_type`, `company`, `date`, `page`, `preview`, `content`, and `citation_id`.

## Required Adapter Decisions

Phase 3 should produce backend SSE payloads that are stable and complete. Phase 4 should add a frontend adapter that maps backend payloads into the current frontend component state.

### Backend → Frontend Type Mapping

| Backend | Frontend |
|---------|----------|
| `financial_report` | `财报` |
| `research_report` | `研报` |
| `news` | `新闻` |
| `chunk_id` / `citation_id` | `Document.id` |
| `title` | `Document.title` |
| `page` + `date` + `source`/`title` | `Document.source` |
| `score` / `rerank_score` | `Document.score` |
| `preview` / `content` | `Document.contentSnippet` |

## Final Phase 3 SSE Contract

The backend query stream should emit events in this order for the imported React frontend:

1. `query_rewrite`
2. `intent_detected`
3. `retrieval_complete`
4. `rerank_complete`
5. `ping`
6. one or more `answer_chunk`
7. `done`

Notes for Phase 4:

- `answer_chunk.text` can be appended directly into the assistant message body.
- `done.citations` is keyed by string citation IDs and maps cleanly to clickable citation spans.
- `error` events should be shown in the existing toast/retry path without changing layout.

## Phase 3 Prep Requirements

Phase 3 should add backend contract examples and/or tests that mirror frontend needs:

- `query_rewrite` must include expanded terms for `Message.queryRewrite`.
- `retrieval_complete` must preserve separate `bm25_results`, `vector_results`, and `fused_top20` arrays.
- `rerank_complete` must include Top 5 items with `citation_id` and full snippet/content.
- `answer_chunk` should stream markdown that can render in ReactMarkdown.
- Citation markup should be frontend-clickable. Preferred compatibility format: `<span class="cite" data-id="1">[1]</span>` or another format that frontend adapter can transform into that shape.
- `done` must include `total_tokens`, `latency_ms`, and `citations` keyed by citation ID.
- `error` must include code/message for toast or retry handling.

## Phase 4 Integration Tasks

When Phase 3 backend query SSE exists, Phase 4 should:

1. Add Vite `/api` proxy to `http://localhost:8000`.
2. Replace `simulateRAGFlow()` with an API client/hook while preserving current UI state shape.
3. Replace `mockLeftDocuments` with `GET /api/documents` mapping.
4. Map `retrieval_complete` BM25/vector outputs into `SidebarRight` arrays.
5. Map `rerank_complete.top5` into rerank cards and citation IDs.
6. Stream `answer_chunk.text` into the active assistant message.
7. Use `done.citations` to support clickable citation highlighting.
8. Add frontend/backend integration smoke tests or a manual checklist for the three demo questions.

## Constraints

- Do not redesign frontend UI unless explicitly requested.
- Keep frontend component visuals intact; build adapters around the existing `Message` and `Document` shapes.
- Backend remains source of truth for retrieval/rerank/citation metadata.

---
*Last updated: 2026-05-13 after importing frontend code*

## Phase 4 Implementation Notes

**Updated:** 2026-05-13 after Phase 4 integration wiring.

Implemented wiring:

- `frontend/vite.config.ts` proxies `/api` to `http://localhost:8000` in Vite dev mode.
- `frontend/src/api/finrag.ts` owns backend payload types, document/retrieval/rerank mappers, `fetchDocuments()`, and fetch-based POST SSE parsing.
- `frontend/src/App.tsx` now calls `GET /api/documents` for the left document library and `POST /api/query` for query execution.
- `frontend/src/components/SidebarLeft.tsx` accepts document props while preserving existing markup and example questions.
- `frontend/src/components/SidebarRight.tsx` and `frontend/src/components/ChatArea.tsx` remain visually unchanged and receive backend-driven state through existing props.

Final event-to-state mapping:

| SSE Event | Frontend State |
| --- | --- |
| `query_rewrite` | `Message.queryRewrite`, stage remains `query` |
| `retrieval_complete` | `bm25Docs`, `vectorDocs`, assistant stage `retrieve` |
| `rerank_complete` | `rerankDocs`, assistant stage `rerank` |
| `answer_chunk` | append to assistant `content`, stage `generate` |
| `done` | assistant stage `done`, `Message.tokens` |
| `error` | assistant stage `done`, Chinese error content |
| `ping` | no visual change |

Fallback behavior:

- Document library falls back to `mockLeftDocuments` if backend document loading fails.
- Retrieval panels reset at query start and repopulate as backend events arrive.
- Query fetch/SSE failures produce an assistant error message instead of crashing the UI.

## Phase 5 Preview Enhancement

- `POST /api/preview-rewrite` is now available for typing preview.
- Preview requests should be debounced and abortable.
- The preview area in `ChatArea` is wired to backend rewrite data while the main SSE flow remains unchanged.
