# Phase 19: Multi-stage Retrieval Cascade Trace - Research

**Researched:** 2026-05-21
**Phase:** 19 - Multi-stage Retrieval Cascade Trace

## Research Goal

Plan how to add observable retrieval cascade traces on top of the existing Phase 17/18 query-plan and route/filter pipeline without changing retrieval behavior or SSE event order.

## Current System Shape

### Query Path

- `backend/app/api/query.py` streams events in this order:
  - `query_rewrite`
  - `intent_detected`
  - `retrieval_complete`
  - `rerank_complete`
  - `ping`
  - `answer_chunk`
  - `done`
- `analyze_query()` produces `QueryRewriteEvent` with an optional `RetrievalPlan`.
- The query API passes `rewrite.plan` into `HybridRetriever.retrieve()`.
- `RerankService().rerank()` runs outside `HybridRetriever`, so rerank and final evidence trace stages should be appended by API/workflow code or a small helper near the API/workflow boundary.

### Retrieval Path

- `HybridRetriever.retrieve(query, top_k=None, plan=None)` currently:
  - chooses route with `choose_route(plan, query)`
  - builds metadata filters with `build_metadata_filters(plan)`
  - runs BM25 search
  - runs vector search
  - runs supplemental/table-fact hits
  - applies metadata filters to BM25/vector/supplemental candidates
  - fuses candidates with `_rrf_fuse()`
  - returns `HybridRetrievalResult`
- `HybridRetrievalResult` already carries Phase 18 route/filter metadata:
  - `route`
  - `route_reason`
  - `applied_filters`
  - `filter_before_count`
  - `filter_after_count`
  - `filters_relaxed`
  - `filter_fallback_reason`
  - channel errors

### Existing API Models

- `RetrievalCompleteEvent` carries retrieval lists and BM25/vector errors.
- `RerankCompleteEvent` carries `top5`, degradation flag, fallback reason, and score source.
- `/api/debug/retrieval` returns retrieval/rerank sections plus Phase 18 route/filter metadata.

## Recommended Implementation Path

### 1. Add Trace Models

Add additive Pydantic models in `backend/app/models/schemas.py` or `backend/app/models/events.py`.

Recommended schema:

```python
class RetrievalCascadeStage(BaseModel):
    name: Literal["query_plan", "metadata_filter", "coarse_recall", "fusion", "rerank", "final_evidence"]
    method: str
    input_count: int = 0
    output_count: int = 0
    degraded: bool = False
    fallback_reason: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

This is sufficient for CASCADE-01/02 and avoids a larger trace abstraction.

### 2. Add Retrieval-Side Trace Capture

Extend `HybridRetrievalResult` with:

```python
cascade_trace: list[RetrievalCascadeStage] = Field/default_factory equivalent
```

Because it is a dataclass, use `field(default_factory=list)` if staying dataclass-based.

Retrieval should append stages:

- `query_plan`
  - method: selected route or `no_plan`
  - input_count: 1
  - output_count: 1
  - metadata: route, route_reason, plan task type/retrieval strategy if available
- `metadata_filter`
  - method: `metadata_pre_filter`
  - input_count/output_count from Phase 18 filter counts
  - degraded/fallback when filters relaxed
  - metadata: applied filters
- `coarse_recall`
  - method: `bm25+vector+supplemental`
  - input_count: 1
  - output_count: total raw candidate count before filtering or sum of channel counts
  - degraded/fallback when BM25/vector errors exist
  - metadata: per-channel counts and errors
- `fusion`
  - method: `rrf`
  - input_count: filtered candidate count
  - output_count: fused count
  - metadata: `rrf_k`, `top_k`

### 3. Append Rerank And Final Evidence Trace

Because rerank is outside retriever:

- Add optional `cascade_trace` fields to `RetrievalCompleteEvent` and/or `RerankCompleteEvent`.
- Prefer including retrieval-side trace in `RetrievalCompleteEvent` and rerank/final evidence stages in `RerankCompleteEvent`. This keeps stage ownership clear and does not add new SSE events.
- `/api/debug/retrieval` can expose a single combined `cascade_trace` field for demo inspection.

Recommended additions:

- `RetrievalCompleteEvent.cascade_trace: list[RetrievalCascadeStage] = []`
- `RerankCompleteEvent.cascade_trace: list[RetrievalCascadeStage] = []`
- `DebugRetrievalResponse.cascade_trace: list[RetrievalCascadeStage] = []`

### 4. Preserve Compatibility

- Do not rename existing event fields.
- Do not add new event names.
- Do not require frontend changes unless TypeScript build has strict event models that need additive optional fields.
- Existing fake retrievers in tests may not define `cascade_trace`; use `getattr(result, "cascade_trace", [])`.

## Testing Strategy

Targeted tests:

- `backend/tests/test_hybrid_retrieval.py`
  - string-only retrieval returns a deterministic cascade trace.
  - plan-aware NVIDIA revenue query includes `query_plan`, `metadata_filter`, `coarse_recall`, and `fusion` stages.
  - filter relaxation appears as degraded/fallback metadata in `metadata_filter`.
- `backend/tests/test_debug_retrieval.py`
  - `/api/debug/retrieval` returns combined trace including `rerank` and `final_evidence`.
  - stage entries have `name`, `method`, `input_count`, `output_count`.
- `backend/tests/test_query_api.py`
  - SSE event order stays unchanged.
  - retrieval/rerank payloads include optional cascade trace fields.
  - fake retrievers without trace still work.

Verification command:

```bash
cd backend && pytest tests/test_hybrid_retrieval.py tests/test_debug_retrieval.py tests/test_query_api.py -q
```

Then run:

```bash
cd backend && pytest -q
```

## Risks And Mitigations

- **Contract drift:** Use additive fields only and preserve event order.
- **Trace inconsistency:** Use a single model and deterministic stage names.
- **Overreach into Phase 20:** Do not alter evidence content or generation prompts.
- **Overreach into Phase 21:** Do not create multiple retrieval passes.
- **Mock compatibility:** Use `getattr(..., [])` when consuming trace from retriever results.

## Recommendation

Implement as one executable plan:

1. Add trace schema and retrieval-side stage capture.
2. Wire trace through debug and SSE payloads with rerank/final evidence stages.
3. Add deterministic regression tests for route/filter/recall/fusion/rerank/final evidence trace presence and event-order compatibility.

## RESEARCH COMPLETE
