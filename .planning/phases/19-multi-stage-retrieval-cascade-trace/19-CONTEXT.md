# Phase 19: Multi-stage Retrieval Cascade Trace - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 19 turns the existing plan-aware retrieval pipeline into an observable multi-stage cascade.

This phase should expose how a query moved through planning/routing, metadata filtering, coarse recall, fusion/lightweight selection, rerank, and final evidence selection. It should not change retrieval semantics beyond adding trace capture and optional response fields.

This phase does not implement evidence compression, iterative retrieval, or hierarchical drill-down. Those remain Phase 20, Phase 21, and Phase 22.

</domain>

<decisions>
## Implementation Decisions

### Trace Contract

- **C-01:** Add a small structured cascade trace model rather than ad-hoc dicts scattered through the retrieval and API layers.
- **C-02:** Each trace stage must include `name`, `input_count`, `output_count`, `method`, and optional degradation/fallback metadata.
- **C-03:** Stage names should be deterministic and demo-friendly: `query_plan`, `metadata_filter`, `coarse_recall`, `fusion`, `rerank`, and `final_evidence`.
- **C-04:** The trace should reuse Phase 17/18 route and filter metadata instead of re-deriving it.

### API And SSE Compatibility

- **C-05:** Expose cascade traces through additive fields only.
- **C-06:** `/api/debug/retrieval` should expose the full trace first.
- **C-07:** `/api/query` may include an optional trace field inside existing retrieval/rerank event payloads, but must preserve existing event names and order.
- **C-08:** Existing frontend consumers must remain valid even if they ignore the new trace fields.

### Retrieval Ownership

- **C-09:** `HybridRetriever.retrieve()` should continue to support string-only callers.
- **C-10:** Retrieval should record trace stages for route/filter/recall/fusion, while rerank/final evidence stages can be appended in API/workflow code where rerank actually runs.
- **C-11:** The trace should capture both normal and degraded paths, including BM25/vector errors and metadata filter relaxation.

### Deferred Work

- **C-12:** Do not compress or rewrite evidence content in this phase.
- **C-13:** Do not add multi-query iterative planning in this phase.
- **C-14:** Do not require frontend visual redesign; optional TypeScript typing is acceptable only if existing frontend types need it.

</decisions>

<specifics>
## Specifics

- Phase 17 added `RetrievalPlan` to `QueryRewriteEvent`.
- Phase 18 added route/filter metadata to `HybridRetrievalResult` and `/api/debug/retrieval`.
- `RetrievalCompleteEvent` currently includes `bm25_results`, `vector_results`, `fused_top20`, `bm25_error`, and `vector_error`.
- `RerankCompleteEvent` currently includes `top5`, `degraded`, `fallback_reason`, and `score_source`.
- Representative Phase 19 tests should cover:
  - NVIDIA FY2026 Q3 revenue table-fact query.
  - CATL / 宁德时代 risk-analysis query.
  - A general or financial-report lookup query.

</specifics>

<deferred>
## Deferred Ideas

- Evidence compression and compact evidence packs — Phase 20.
- Agentic iterative retrieval steps — Phase 21.
- Hierarchical chunking and drill-down retrieval — Phase 22.

</deferred>

---

*Phase: 19-multi-stage-retrieval-cascade-trace*
*Context gathered: 2026-05-21*
