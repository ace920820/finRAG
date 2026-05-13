# Phase 5: P1 Enhancements - Context

**Gathered:** 2026-05-13  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 adds only high-value, low-risk enhancements on top of the completed MVP integration path. The core backend query flow and frontend/backend联调 must remain unchanged. This phase should focus on query rewrite preview and other small financial-domain quality improvements only if they do not destabilize the demo.

</domain>

<decisions>
## Implementation Decisions

### Preview Rewrite
- **D-01:** Add optional `POST /api/preview-rewrite` returning expanded terms and detected entities.
- **D-02:** Reuse the existing deterministic query analysis logic rather than adding a new LLM-based preview flow.
- **D-03:** The response must be lightweight and safe to call frequently from the frontend typing preview.

### Frontend Preview UX
- **D-04:** Enable the frontend query rewrite preview using backend data instead of the current static mock preview.
- **D-05:** Debounce preview requests so typing does not spam the backend.
- **D-06:** Preserve the existing UI layout and input affordance; only the preview data source should change.

### Scope Control
- **D-07:** Do not change the main `POST /api/query` SSE workflow.
- **D-08:** Do not redesign the frontend or introduce new state-management libraries.
- **D-09:** Do not add live provider requirements for preview functionality.
- **D-10:** Do not pursue numeric consistency checks or recency weighting unless they can be implemented without broad changes; treat them as deferred.

### the agent's Discretion
- The agent may choose the exact preview response schema as long as it exposes expanded terms and detected entities.
- The agent may choose whether the frontend preview shows only a compact keyword list or also a short entity label.
- The agent may add a minimal backend helper for entity extraction if needed for preview response clarity.

</decisions>

<specifics>
## Specific Ideas

- The current frontend `ChatArea` already has a preview area and simple typing indicator; it can be wired to live preview data with a debounce.
- Query analysis already expands aliases for “贵州茅台” and “宁德时代/CATL”; those outputs can seed the preview response.
- A compact `detected_entities` array or `entities` object will help the frontend show a more informative preview without changing layout.

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project And Scope
- `.planning/PROJECT.md` — backend ownership and frontend integration boundary.
- `.planning/ROADMAP.md` — Phase 5 goal and success criteria.
- `.planning/REQUIREMENTS.md` — `API-10` and optional v2 quality enhancement references.
- `.planning/STATE.md` — Current project phase and state.
- `AGENTS.md` — Required `karpathy-guidelines` behavior.

### Prior Phases
- `.planning/phases/04-integration-and-demo-hardening/04-VERIFICATION.md` — completed frontend/backend integration baseline.
- `.planning/phases/03-agent-workflow-and-sse-query-api/03-VERIFICATION.md` — backend SSE contract and stage mapping baseline.
- `backend/app/core/agent/query_analysis.py` — existing deterministic query rewrite and intent detection.
- `backend/app/api/query.py` — stable query SSE workflow that must remain unchanged.

### Frontend Source
- `frontend/src/components/ChatArea.tsx` — typing preview and message rendering hook point.
- `frontend/src/App.tsx` — current backend-driven integration shell.
- `frontend/src/api/finrag.ts` — central adapter module for backend calls.

</canonical_refs>

<code_context>
## Existing Code Insights

### Backend
- `analyze_query()` already returns `QueryRewriteEvent` and `IntentDetectedEvent`.
- The preview endpoint can likely reuse deterministic alias expansion and sub-query logic.
- The current main query workflow should remain untouched to protect the demo path.

### Frontend
- `ChatArea` already has a typing preview area and a visible query input debounce concept.
- The preview text is currently static and should be replaced with live backend preview data.
- Existing `npm run lint` and `npm run build` are the right validation gates for frontend changes.

</code_context>

<deferred>
## Deferred Ideas

- Numeric consistency checking.
- Recency decay / time-sensitive rerank.
- Entity metadata enrichment inside indexed chunks.
- Any changes to the main SSE workflow or retrieval stack.

</deferred>

---

*Phase: 05-p1-enhancements*
*Context gathered: 2026-05-13*
