# Phase 3 Research: Agent Workflow And SSE Query API

**Created:** 2026-05-13  
**Status:** Ready for planning

## Research Goal

Identify the minimum backend implementation needed to deliver a stable `POST /api/query` SSE workflow that composes Phase 2 retrieval/rerank services, Qwen Plus-compatible generation, source-grounded citations, and frontend-ready event payloads without redesigning the imported React UI.

## Inputs Reviewed

- `.planning/PROJECT.md` — backend ownership, demo value, model-provider direction.
- `.planning/ROADMAP.md` — Phase 3 goal and frontend integration dependency.
- `.planning/REQUIREMENTS.md` — `AGNT-*` and `API-*` requirements assigned to Phase 3.
- `.planning/phases/03-agent-workflow-and-sse-query-api/03-CONTEXT.md` — locked decisions for this phase.
- `.planning/frontend-integration-readiness.md` — imported frontend mock contract and Phase 4 adapter needs.
- `backend/app/models/events.py` — existing SSE event payload models.
- `backend/app/api/debug.py` — retrieval/rerank JSON shape that can be reused for query orchestration.
- `backend/app/core/retrieval/hybrid.py` — BM25/vector/RRF retrieval service.
- `backend/app/core/retrieval/rerank_service.py` — rerank top-5 and fallback behavior.
- `backend/app/core/providers/text.py` and `backend/app/core/providers/rerank.py` — current text-provider seam.
- `frontend/src/App.tsx`, `frontend/src/components/ChatArea.tsx`, `frontend/src/components/SidebarRight.tsx` — current mock-driven frontend expectations.

## Existing Assets

### Backend

- FastAPI app factory already includes router registration pattern in `backend/app/main.py`.
- `QueryRequest`, `RetrievalResultItem`, `RerankResultItem`, and `CitationMetadata` already exist in `backend/app/models/schemas.py`.
- `QueryRewriteEvent`, `RetrievalCompleteEvent`, `RerankCompleteEvent`, `IntentDetectedEvent`, `AnswerChunkEvent`, `DoneEvent`, `ErrorEvent`, and `PingEvent` already exist in `backend/app/models/events.py`.
- Phase 2 retrieval emits separate BM25, vector, and fused lists, matching the frontend right-panel needs.
- Phase 2 rerank emits citation IDs and degrades gracefully when the live reranker fails.
- Tests already use deterministic mock providers and should remain offline.

### Frontend

- Frontend state already has stages equivalent to query rewrite, retrieval, rerank, generation, and done.
- The right panel already expects distinct BM25/vector/rerank arrays.
- Citation click behavior works with `<span class="cite" data-id="N">[N]</span>`.
- Phase 4 should add adapters and Vite proxy; Phase 3 only needs stable backend event contracts and examples.

## Recommended Architecture

### 1. Query Workflow Service

Create a small orchestration layer under `backend/app/core/agent/`:

- `query_analysis.py` — deterministic query rewrite and simple intent classification.
- `prompts.py` — prompt builder that formats user query, intent, and reranked evidence.
- `generator.py` — answer generation service wrapping the configured text provider and mock fallback.
- `workflow.py` — composes rewrite, retrieval, rerank, generation, citations, latency, and degraded metadata.

Rationale: this keeps `backend/app/api/query.py` thin and avoids putting business workflow into the route handler.

### 2. Text Provider Contract

Current text provider is only a stub seam. Phase 3 should make it useful without overbuilding:

- Keep `text_provider=mock` as the default.
- For mock mode, generate deterministic Markdown grounded in top rerank results and include citation spans.
- For Bailian mode, use the existing OpenAI-compatible base URL/API key/model config and call Qwen Plus through a provider method that can return one complete answer string.
- Do not implement provider-level streaming yet; the SSE endpoint can chunk the returned string deterministically for demo stability.

Rationale: one-shot generation plus backend chunking is sufficient for an MVP SSE demo and keeps tests deterministic.

### 3. SSE Formatter

Add a tiny formatter utility that converts event name + Pydantic payload into Server-Sent Events:

```text
event: query_rewrite
data: {...}

```

Recommended event order:

1. `query_rewrite`
2. `intent_detected`
3. `retrieval_complete`
4. `rerank_complete`
5. zero or more `answer_chunk`
6. `done`

Emit `ping` opportunistically between longer stages if feasible. Tests should require the event model exists and at least one ping/error path is supported, but should not make timing-sensitive assertions.

### 4. Graceful Degradation

- Query rewrite and intent detection should always be deterministic local logic in Phase 3.
- Retrieval failures should produce an `error` event because answer generation has no evidence.
- Rerank failures are already degraded by `RerankService`; preserve this behavior and include enough final metadata for debugging.
- Generation failures should produce a deterministic fallback answer from evidence if possible; otherwise emit an `error` event.

### 5. Citation Contract

- Use `citation_id` from rerank top-5 as the stable source ID.
- Answer text should include clickable-compatible citation spans: `<span class="cite" data-id="1">[1]</span>`.
- `done.citations` should be keyed by string IDs (`"1"`, `"2"`) and contain `CitationMetadata`.
- Avoid inventing frontend-only document shapes in backend; Phase 4 adapters will map backend schema to current React types.

## Testing Strategy

Add focused backend tests:

- Unit tests for query rewrite and intent classification.
- Unit tests for SSE formatting.
- Unit tests for mock answer generation and citation metadata.
- Endpoint test for `POST /api/query` verifying event order and required payload keys.
- Degradation test for generation failure or provider fallback without network/API keys.

Keep full validation command:

```bash
cd backend && python3 -m pytest
```

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| SSE tests become brittle due to timing | Parse event names/data from full response; avoid timing assertions. |
| Live Qwen API shape differs from assumptions | Keep live provider behind config and do not require it for tests; use OpenAI-compatible client path already established. |
| Backend drifts toward frontend-specific models | Emit canonical backend schemas; document Phase 4 adapter mapping separately. |
| Query workflow grows into complex agent framework | Keep deterministic local rewrite/intent and a single prompt builder; no graph framework. |
| Citations become hard to click in frontend | Include citation spans in answer chunks and authoritative citation map in `done`. |

## Recommendation

Plan Phase 3 as three focused execution plans:

1. **Agent workflow primitives** — query analysis, prompt builder, generation service, citations.
2. **SSE query API** — route, formatter, event stream order, graceful error behavior.
3. **Contract tests and integration readiness** — backend tests and documentation examples for Phase 4 frontend wiring.

This is the smallest backend-first slice that satisfies Phase 3 while preserving Phase 4 as a frontend adapter task.
