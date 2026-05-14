# Phase 3 Baseline Review — Agent Workflow & SSE Query API

Read-only baseline regression review of the agent workflow primitives and `/api/query` SSE transport.

## Scope

PLAN: `.planning/phases/03-agent-workflow-and-sse-query-api/03-01-PLAN.md`

Re-validate that:

- `analyze_query()` returns deterministic intent/rewrite.
- SSE event names and shapes still match the frontend contract.
- Citation metadata is still keyed by string citation IDs and matches `<span class="cite" data-id="N">`.
- Default code path does not need `FINRAG_MODEL_API_KEY`.

## Files Audited

- `backend/app/core/agent/{query_analysis,prompts,generator,workflow}.py`
- `backend/app/api/query.py`
- `backend/app/core/sse.py`
- `backend/app/models/events.py`

## Verification Run

- `python3 -m pytest -q tests/test_query_analysis.py tests/test_agent_workflow.py tests/test_query_api.py tests/test_sse_formatter.py` (run together with full suite, all green).
- Hand-checked SSE event set in `query.py`: `query_rewrite`, `intent_detected`, `retrieval_complete`, `rerank_complete`, `ping`, `answer_chunk`, `done`, `error` — full set still emitted.
- Citation render path: `agent/generator.py:50` and `providers/rerank.py:77,81` emit `<span class="cite" data-id="N">[N]</span>`, frontend `finrag.ts:117-121` still parses these events. Consistent.

## Findings

### Blocker

None at the Phase 3 boundary. The empty-retrieval issue surfaced under Phase 2 (Blocker B2) propagates here, but the agent workflow itself behaves correctly under the documented contract.

### Important

- **[Important] `query.py` reaches into `workflow.py` private helpers**
  - File: `backend/app/api/query.py:11` imports `_build_citations`, `_estimate_tokens`, `_retrieval_query` from `app.core.agent.workflow`.
  - PLAN said the workflow should be transport-independent and the SSE route thin. Reusing private `_`-prefixed helpers across modules couples the transport layer to internals. Either promote them (rename without leading underscore) or call `QueryWorkflow().run()` from the SSE route and stream the structured result.

- **[Important] `query.py` exception path emits stale `RerankCompleteEvent`**
  - File: `backend/app/api/query.py:65-72`.
  - When retrieval/rerank fails, the route yields `format_sse_event("rerank_complete", RerankCompleteEvent(top5=rerank.top5, ...))` where `rerank` is the still-empty default-constructed event. Frontend will see two `rerank_complete` events in some failure modes (one from inside the `try` block already and one in the `except`). Low-risk because the `try` failure usually happens before the first emit, but worth tightening.

### Nice-to-have

- **[Nice-to-have] Duplicate orchestration logic between `query.py` and `agent/workflow.py`**
  - The SSE route reimplements the rewrite → retrieve → rerank → generate sequence already in `QueryWorkflow.run`. Two implementations to keep in sync. Acceptable for v1.0 demo, worth consolidating in or after Phase 16.

- **[Nice-to-have] `analyze_query` default fallback intent is `analytical`**
  - File: `backend/app/core/agent/query_analysis.py:43`.
  - Some short factual queries with no `_FACTUAL_HINTS` will be classified as analytical. Not a Phase 3 PLAN violation; consider adjusting once Phase 16 introduces numeric/metric routing.

- **[Nice-to-have] `prompts.build_generation_prompt` always appends "请给出简洁、可展示的中文 Markdown 回答"**
  - English/mixed-language reports (NVIDIA, TSMC) might benefit from intent-conditional language hint once live LLM is used. Out of scope for baseline review.

## Phase 15/16 Risk Notes

- `RerankResultItem.content` is concatenated into the prompt as a single string. When Phase 15 lands table-row / table-summary chunks, prompts will grow long unless evidence formatting differentiates table vs text. Consider a `chunk_type`-aware prompt branch in Phase 16.
- `CitationMetadata.section` is `Optional[str]` and currently always `None` from `workflow._build_citations`. Phase 16 should populate this for table evidence to keep citations human-readable.
- `DoneEvent.citations: dict[str, CitationMetadata]` is keyed by string rank (`"1"`, `"2"`, ...). When introducing structured table citations, keep this contract or version it explicitly.

## Recommended Follow-up

1. Decide between two approaches and consolidate:
   - Option A: have `/api/query` call `QueryWorkflow().run()` and stream from its result.
   - Option B: promote workflow helpers to public (`build_citations`, `estimate_tokens`, `retrieval_query`).
2. Make the exception path emit `rerank_complete` exactly once. **(Important)**
3. Defer prompt/citation enrichment until Phase 16 starts the table-aware QA work.
