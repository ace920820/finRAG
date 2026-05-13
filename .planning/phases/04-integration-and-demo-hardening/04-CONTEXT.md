# Phase 4: Integration And Demo Hardening - Context

**Gathered:** 2026-05-13  
**Status:** Ready for planning  
**Source:** Default recommendations from prior user decisions and imported frontend state

<domain>
## Phase Boundary

Phase 4 connects the imported React/Vite frontend to the completed FastAPI backend contracts. It replaces local mock RAG simulation with backend API/SSE adapters, maps backend document/retrieval/citation payloads into existing frontend state shapes, and validates the three demo questions end-to-end.

This phase must not redesign the frontend UI or change the externally delivered interaction model. Frontend changes should be adapter-level and minimal: API client, type mapping, state wiring, proxy config, and smoke validation.

</domain>

<decisions>
## Implementation Decisions

### Frontend Integration Scope
- **D-01:** Preserve the current imported React component layout and visual design.
- **D-02:** Replace `simulateRAGFlow()` with a backend API/SSE-driven flow in or near `frontend/src/App.tsx`.
- **D-03:** Add frontend adapter/client modules instead of pushing backend-specific field names throughout UI components.
- **D-04:** Keep existing frontend `Message` and `Document` shapes as the UI-facing state model.
- **D-05:** Do not implement a new design system, routing layer, global state library, or frontend redesign.

### Backend Contract Usage
- **D-06:** Use `GET /api/documents` to populate the left document library.
- **D-07:** Use `POST /api/query` as the only query execution endpoint for Phase 4.
- **D-08:** Parse SSE events in the Phase 3 order: `query_rewrite`, `intent_detected`, `retrieval_complete`, `rerank_complete`, `ping`, `answer_chunk`, `done`, with `error` as failure path.
- **D-09:** Map `retrieval_complete.bm25_results` and `vector_results` into right-panel BM25/vector document arrays.
- **D-10:** Map `rerank_complete.top5` into right-panel rerank cards and citation IDs.
- **D-11:** Append `answer_chunk.text` to the active assistant message without reformatting content beyond what ReactMarkdown already supports.
- **D-12:** Use `done.total_tokens`, `done.latency_ms`, and `done.citations` for final message metadata and citation support where it fits existing UI state.

### Demo Reliability
- **D-13:** Keep frontend mock data as a fallback/development fallback only if the backend request fails before a useful stream starts.
- **D-14:** Surface backend `error` SSE events as user-visible assistant error content without crashing the UI.
- **D-15:** Ensure backend remains offline-testable with mock providers; Phase 4 does not require live Alibaba Cloud credentials.
- **D-16:** Validate all three demo questions through local backend + frontend build/lint checks.

### the agent's Discretion
- The agent may choose exact adapter file names under `frontend/src/`.
- The agent may choose whether to keep minimal fallback mocks or remove only the simulated timer flow.
- The agent may add lightweight frontend tests only if the existing project can support them without new heavyweight setup.
- The agent may improve backend tests for contract coverage if integration reveals missing fields, but should not expand backend features beyond Phase 4 needs.

</decisions>

<specifics>
## Specific Ideas

- `frontend/src/App.tsx` currently owns message state, right-panel document state should be introduced there or through a small hook.
- `frontend/src/components/SidebarLeft.tsx` currently imports `mockLeftDocuments`; it should accept document list props while preserving markup.
- `frontend/src/components/SidebarRight.tsx` already accepts BM25/vector/rerank arrays and should not need visual changes.
- `frontend/src/components/ChatArea.tsx` already parses clickable citation spans and should continue to receive markdown content with span citations.
- `frontend/vite.config.ts` should proxy `/api` to the backend dev server at `http://localhost:8000`.
- Backend `doc_type` values map to frontend Chinese labels: `financial_report → 财报`, `research_report → 研报`, `news → 新闻`.

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project And Scope
- `.planning/PROJECT.md` — backend ownership, frontend boundary, and core value.
- `.planning/ROADMAP.md` — Phase 4 goal and success criteria.
- `.planning/REQUIREMENTS.md` — `INTG-*` requirements.
- `.planning/STATE.md` — Current project phase and state.
- `AGENTS.md` — Required `karpathy-guidelines` coding behavior.

### Integration Contracts
- `.planning/frontend-integration-readiness.md` — canonical backend/frontend adapter checklist.
- `.planning/phases/03-agent-workflow-and-sse-query-api/03-VERIFICATION.md` — completed backend SSE contract verification.
- `backend/app/api/query.py` — `POST /api/query` SSE endpoint.
- `backend/app/core/sse.py` — SSE frame formatting and event behavior.
- `backend/app/models/events.py` — SSE payload models.
- `backend/app/models/schemas.py` — document/retrieval/citation schemas.

### Frontend Source
- `frontend/src/App.tsx` — current mock RAG flow to replace.
- `frontend/src/types.ts` — UI state types to preserve.
- `frontend/src/components/SidebarLeft.tsx` — document library currently mock-driven.
- `frontend/src/components/SidebarRight.tsx` — retrieval/rerank display props.
- `frontend/src/components/ChatArea.tsx` — message/stage/citation rendering.
- `frontend/src/data/mock.ts` — fallback/mock shape examples.
- `frontend/vite.config.ts` — Vite dev proxy target.

</canonical_refs>

<code_context>
## Existing Code Insights

### Backend
- Phase 3 SSE endpoint streams all required frontend events and passes backend tests.
- Backend query API is mock-provider safe and does not need live model credentials.
- `GET /api/documents` already exists for left sidebar document metadata.

### Frontend
- Frontend is a Vite React app with TypeScript and `npm run lint` mapped to `tsc --noEmit`.
- `App.tsx` currently uses timer-based `simulateRAGFlow()` and mock retrieval arrays.
- `SidebarRight` already accepts real arrays through props, so the integration mostly needs state wiring and adapter mapping.
- `SidebarLeft` needs to accept backend-loaded documents rather than importing mock documents directly.

</code_context>

<deferred>
## Deferred Ideas

- Frontend UI redesign or component restyling.
- Full citation source drawer beyond existing highlight behavior.
- Production deployment and authentication.
- Live Alibaba Cloud credential smoke tests.
- Advanced retry/backoff/circuit-breaker behavior.
- Optional `/api/preview-rewrite` endpoint, which remains Phase 5.

</deferred>

---

*Phase: 04-integration-and-demo-hardening*  
*Context gathered: 2026-05-13*
