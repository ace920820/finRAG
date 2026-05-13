# Phase 3: Agent Workflow And SSE Query API - Context

**Gathered:** 2026-05-13  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers the core `POST /api/query` SSE workflow for FinRAG. It should orchestrate query rewrite, hybrid retrieval, rerank, optional intent detection, streamed Markdown answer chunks, final completion metadata, heartbeat events, and safe error events.

This phase does **not** redesign the frontend UI. It exists to provide a stable backend stream contract that the imported React app can adapt to in Phase 4 using its existing component layout and state model.

</domain>

<decisions>
## Implementation Decisions

### Query Workflow Shape
- **D-01:** Implement `POST /api/query` as the primary frontend/backend integration endpoint.
- **D-02:** Emit `query_rewrite` as an explicit SSE event so the frontend can surface query expansion in the current assistant stage UI.
- **D-03:** Keep the workflow order stable: query rewrite → retrieval → rerank → generation chunks → done or error.
- **D-04:** Support `session_id` as a lightweight field in the request and preserve it for future multi-turn expansion, but do not build full conversation memory yet.

### Model Provider Strategy
- **D-05:** Use Alibaba Cloud Bailian / DashScope-compatible API providers for LLM generation, matching the Phase 2 provider strategy.
- **D-06:** Default text generation model should be Qwen Plus.
- **D-07:** Provider selection must remain config-driven and reuse the existing `FINRAG_` settings pattern and `.env.example` placeholder approach.
- **D-08:** Automated tests must remain offline-safe by default; live provider calls are only for explicit manual smoke testing.

### Response And Citation Shape
- **D-09:** Generated Markdown should remain source-grounded and citation-aware, with each factual statement traceable to chunk metadata.
- **D-10:** Citation formatting should be compatible with both plain `[1]` style markers and frontend-clickable `<span class="cite" data-id="1">[1]</span>` style markup.
- **D-11:** The final `done` event must include `latency_ms`, `total_tokens`, and `citations` keyed by citation ID.
- **D-12:** The `error` event must include a machine-readable `code` and user-facing `message` suitable for the current frontend toast/retry behavior.
- **D-13:** The `answer_chunk` stream should preserve Markdown that renders correctly in ReactMarkdown, including source citations.

### Frontend Integration Contract
- **D-14:** Backend SSE payloads must match the imported frontend's current stage model: query, retrieve, rerank, generate, done.
- **D-15:** Backend retrieval and rerank payloads should remain separate and metadata-rich so Phase 4 can map them into the existing right sidebar panels.
- **D-16:** `GET /api/documents` remains the left sidebar source of truth.
- **D-17:** Phase 3 should provide backend fixtures/tests/examples that mirror the imported frontend's current mock contract, so Phase 4 can replace mocks with adapters instead of redesigning the UI.

### Error And Heartbeat Policy
- **D-18:** Emit `ping` heartbeats during long-running query streams.
- **D-19:** Prefer graceful degradation over hard failure when a downstream provider can be bypassed or when partial outputs are still useful.
- **D-20:** Do not add retry complexity beyond what is needed for clear error surfacing and stable demo behavior.

### Scope Control
- **D-21:** Do not add full multi-turn memory or conversation summarization in Phase 3.
- **D-22:** Do not redesign the frontend UI or component structure in Phase 3.
- **D-23:** Do not add new retrieval algorithms or expand the vector/index layer further; Phase 2 already locked that.
- **D-24:** Do not introduce production observability or deployment concerns.

### the agent's Discretion
- The agent may choose the exact internal orchestrator/service names for query workflow, generation, and SSE event assembly.
- The agent may choose whether to expose a small internal debug/helper function for building response chunks, as long as the public contract stays stable.
- The agent may choose how to map source chunks into the generated answer stream, provided the citation contract remains consistent.

</decisions>

<specifics>
## Specific Ideas

- The imported frontend currently simulates the full flow in `frontend/src/App.tsx` and expects stage updates in the current assistant message.
- `frontend/src/components/ChatArea.tsx` already renders stage labels and clickable citations, so the backend should preserve the shape needed for those interactions.
- `frontend/src/components/SidebarRight.tsx` already expects separated BM25, vector, and rerank payloads; Phase 3 should keep the SSE payloads compatible with those lists.
- `frontend/src/components/SidebarLeft.tsx` still uses mock document metadata, but the left-side data source is already known to be `GET /api/documents`.
- Preferred citation compatibility: emit backend citation IDs in a stable structure and keep the markdown stream easy to post-process into clickable span markup.

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project And Scope
- `.planning/PROJECT.md` — Project context, backend ownership, frontend boundary, and core value.
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria, and frontend integration prep notes.
- `.planning/REQUIREMENTS.md` — `AGNT-*` and `API-*` requirements mapped to this phase.
- `.planning/STATE.md` — Current project phase and execution state.

### Prior Phases
- `.planning/phases/01-backend-foundation-and-demo-data/01-CONTEXT.md` — Backend-first scope, fixture strategy, and contract-first decisions.
- `.planning/phases/02-hybrid-retrieval-and-rerank/02-CONTEXT.md` — Bailian provider strategy, retrieval/rerank boundaries, and debug API setup.
- `.planning/phases/02-hybrid-retrieval-and-rerank/02-03-SUMMARY.md` — Rerank fallback and debug retrieval behavior already implemented.

### Frontend Integration Prep
- `.planning/frontend-integration-readiness.md` — Canonical adapter checklist for matching the imported React frontend.
- `frontend/src/App.tsx` — Current mock flow and stage transitions.
- `frontend/src/components/ChatArea.tsx` — Citation and stage rendering expectations.
- `frontend/src/components/SidebarRight.tsx` — Retrieval panel data expectations.
- `frontend/src/components/SidebarLeft.tsx` — Left document library expectations.

### Source Requirements
- `FinRAG_需求文档.md` — Original SSE query workflow, citation, and frontend interaction requirements.

### Existing Code
- `backend/app/models/events.py` — Existing future SSE event models.
- `backend/app/models/schemas.py` — Retrieval and citation payload schemas.
- `backend/app/api/debug.py` — Current debug retrieval endpoint that can inform SSE assembly.
- `backend/app/core/retrieval/hybrid.py` — Retrieval-stage outputs available to the workflow.
- `backend/app/core/retrieval/rerank_service.py` — Rerank fallback and citation-ready top 5 results.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/events.py` already defines the Phase 3 SSE payload shapes.
- `backend/app/core/retrieval/hybrid.py` already produces BM25/vector/fused result lists in frontend-observable form.
- `backend/app/core/retrieval/rerank_service.py` already produces citation-ready Top 5 results with fallback.
- `backend/app/api/debug.py` already exposes a retrieval/rerank JSON shape that can be used as a stepping stone toward SSE.

### Established Patterns
- The backend is already fixture-backed, config-driven, and offline-testable.
- Python 3.9-compatible typing style is required in this repository.
- `FINRAG_` config prefix and `backend/app/data/index` / `backend/app/data/processed` storage conventions are established.

### Integration Points
- `POST /api/query` should compose `query_rewrite`, `retrieval_complete`, `rerank_complete`, `answer_chunk`, `done`, `error`, and `ping` using the existing retrieval and rerank services.
- The frontend currently expects staged assistant progress plus Markdown answer chunks and clickable citations.
- Phase 4 will replace frontend mock timers with API/SSE wiring rather than changing the UI layout.

</code_context>

<deferred>
## Deferred Ideas

- Full multi-turn conversation memory — later phase or follow-up iteration.
- Query rewrite preview as a separate API endpoint — optional later enhancement.
- Advanced retry policies and provider circuit breaking — unnecessary for the current demo MVP.
- UI redesign or richer citation panel visuals — owned by the frontend team and out of scope here.
- Additional retrieval algorithms beyond the locked BM25/vector/RRF stack — not part of this phase.

</deferred>

---

*Phase: 03-agent-workflow-and-sse-query-api*  
*Context gathered: 2026-05-13*
