# Phase 21: Agentic Iterative Retrieval Demo Mode - Research

**Researched:** 2026-05-21
**Phase:** 21 - Agentic Iterative Retrieval Demo Mode

## Research Goal

Plan a lightweight iterative retrieval mode that demonstrates purposeful multi-step evidence gathering for complex financial analysis questions while preserving the existing single-pass path for factual/table-fact lookup.

## Current System Shape

### Query Planning

- `backend/app/core/agent/query_analysis.py` builds a deterministic `RetrievalPlan`.
- Analytical/reasoning task types already exist:
  - `risk_analysis`
  - `causal_analysis`
  - `trend_analysis`
  - `comparison`
- Factual and table-fact numeric lookup are represented through `metric_lookup` plus `table_fact_first` routing.

### Retrieval And Trace

- `HybridRetriever.retrieve(query, plan=...)` is plan-aware and returns `HybridRetrievalResult`.
- Retrieval results include Phase 18 route/filter metadata:
  - `route`
  - `route_reason`
  - `applied_filters`
  - filter counts and relaxation/fallback metadata
- Phase 19 added `cascade_trace` for retrieval stages and rerank/final-evidence stages.
- Existing retrieval stage order in tests is:
  - `query_plan`
  - `coarse_recall`
  - `metadata_filter`
  - `fusion`

### Generation And Evidence Packing

- Phase 20 added `build_evidence_pack()` in `backend/app/core/agent/context_builder.py`.
- `/api/query` and `QueryWorkflow.run()` currently run one retrieve pass, rerank `fused_top20`, build an evidence pack from rerank top5, generate, then build citations.
- `/api/debug/retrieval` has a parallel retrieval/rerank/debug path that exposes combined cascade trace.

### API Compatibility Boundary

- Existing `/api/query` event order is fixed:
  - `query_rewrite`
  - `intent_detected`
  - `retrieval_complete`
  - `rerank_complete`
  - `ping`
  - `answer_chunk*`
  - `done`
- Phase 21 should expose iterative retrieval only through additive fields on existing payloads and debug responses.
- No new SSE event names are required.

## Recommended Implementation Path

### 1. Add A Small Deterministic Retrieval Planner

Create `backend/app/core/agent/retrieval_planner.py`.

Recommended public functions:

```python
ITERATIVE_TASK_TYPES = {"risk_analysis", "causal_analysis", "trend_analysis", "comparison"}

def should_use_iterative_retrieval(plan: RetrievalPlan | None) -> bool: ...
def plan_iterative_retrieval(query: str, plan: RetrievalPlan | None) -> IterativeRetrievalTrace: ...
```

Keep this module deterministic and rule-based. It should not call an LLM.

Recommended step purposes:

- `background_facts`
- `risk_or_driver_evidence`
- `cross_check`

The planner should produce at most 3 steps and may produce fewer when the plan lacks enough signals.

### 2. Add Additive Iterative Trace Models

Add small schema models in `backend/app/models/schemas.py` because they will be API-visible through event/debug payloads:

```python
IterativeRetrievalStepPurpose = Literal[
    "background_facts",
    "risk_or_driver_evidence",
    "cross_check",
]

class IterativeRetrievalStep(BaseModel):
    index: int
    purpose: IterativeRetrievalStepPurpose
    retrieval_query: str
    route: str | None = None
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    selected_evidence_ids: list[str] = Field(default_factory=list)
    selected_evidence: list[dict[str, Any]] = Field(default_factory=list)
    cascade_trace: list[RetrievalCascadeStage] = Field(default_factory=list)
    degraded: bool = False
    fallback_reason: str | None = None

class IterativeRetrievalTrace(BaseModel):
    enabled: bool = False
    degraded: bool = False
    fallback_reason: str | None = None
    steps: list[IterativeRetrievalStep] = Field(default_factory=list)
```

Add optional `iterative_trace` fields to `RetrievalCompleteEvent` and debug response models. Prefer not to add it to `RerankCompleteEvent` unless needed, because iterative trace describes evidence collection before rerank.

### 3. Centralize Retrieval/Rerank Execution Before Adding Iteration

`/api/query`, `QueryWorkflow.run()`, and `/api/debug/retrieval` currently duplicate retrieval/rerank/evidence-pack orchestration.

The lowest-risk path is to add a helper in `backend/app/core/agent/workflow.py` or a narrow sibling module. It should:

- run normal single-pass retrieval/rerank;
- optionally run iterative retrieval first when eligible;
- merge and dedupe step candidates before final rerank;
- return retrieval event payload, rerank event payload, evidence pack/items, and trace metadata.

This avoids implementing iterative behavior three different times and lowers SSE/debug parity risk.

### 4. Iterative Step Execution

For eligible plans:

1. Build step queries using the original query, entities, metrics, task type, and existing expanded/sub-query terms where useful.
2. Execute each step with `HybridRetriever.retrieve(step_query, plan=plan)`.
3. Record:
   - purpose
   - generated retrieval query
   - route
   - applied filters
   - selected evidence IDs
   - compact top evidence summaries
   - step-level cascade trace
4. Merge all `fused_top20` items deterministically.
5. Dedupe by `chunk_id` first, then by table fact identity where available.
6. Rerank the merged candidate set once with the original user query.

Do not build independent answers per step. Phase 20 evidence packs remain the final generation input.

### 5. Fallback Behavior

Fallback to the normal single-pass cascade when:

- iterative planning raises or returns no steps;
- any required iterative step fails;
- all iterative steps return no candidate evidence;
- the plan is not eligible.

Expose fallback reason using one of:

- `iterative_planning_failed`
- `iterative_step_failed`
- `iterative_no_evidence`
- `iterative_not_applicable`

Simple factual and table-fact queries should appear as single-pass behavior. For API observability, either omit `iterative_trace` or include `enabled=false`; tests should lock one behavior.

Recommendation: include `iterative_trace` only when iterative mode is attempted or explicitly degraded. This keeps simple factual payloads minimal while remaining additive.

## Testing Strategy

Add focused tests:

- `backend/tests/test_retrieval_planner.py`
  - CATL risk query is eligible and produces 2-3 purposeful steps.
  - causal/reasoning query produces deterministic step purposes and queries.
  - NVIDIA revenue/table-fact lookup is not eligible.
  - maximum step count is 3.
- `backend/tests/test_agent_workflow.py`
  - analytical query returns an iterative trace and final evidence/citations.
  - factual/table query stays single-pass.
  - forced iterative planning or step failure falls back to single-pass with visible reason.
- `backend/tests/test_query_api.py`
  - SSE event names/order remain unchanged.
  - `retrieval_complete` includes additive iterative trace for eligible analytical queries.
  - NVIDIA revenue answer and table citation metadata remain intact.
- `backend/tests/test_debug_retrieval.py`
  - debug response surfaces iterative steps clearly and preserves cascade trace.

Verification:

```bash
cd backend && pytest tests/test_retrieval_planner.py tests/test_agent_workflow.py tests/test_query_api.py tests/test_debug_retrieval.py -q
cd backend && pytest -q
rg "parent_id|chunk_level|drill_down|hierarchical" backend/app backend/tests
```

## Risks And Mitigations

- **SSE regression:** expose data only through existing `retrieval_complete` payload fields and assert event order in tests.
- **Numeric QA regression:** gate iterative retrieval strictly by task type and keep `metric_lookup` / `table_fact_first` single-pass.
- **Trace confusion:** keep `cascade_trace` unchanged and put iterative details in a separate optional `iterative_trace`.
- **Candidate duplication/noise:** dedupe merged candidates deterministically before rerank and keep final generation through Phase 20 evidence packs.
- **Overbuilding agent behavior:** keep planning rule-based, limited to 3 steps, with no LLM planner loop.
- **Scope creep into Phase 22:** do not add hierarchy metadata, parent/child retrieval, drill-down, or corpus/index rebuild work.

## Recommendation

Implement Phase 21 as one executable plan:

1. Add trace schemas and deterministic retrieval planner tests.
2. Add planner implementation and a shared single-pass/iterative retrieval execution helper.
3. Wire workflow, streaming API, and debug endpoint through the helper using additive fields only.
4. Add fallback and regression tests for analytical iterative mode, factual single-pass behavior, table-fact numeric QA, and unchanged SSE order.

## Validation Architecture

The validation focus is behavioral, not visual:

- eligibility matrix proves only intended task types trigger iteration;
- step trace contract proves demo observability;
- fallback tests prove degradation to normal cascade;
- end-to-end API tests prove event compatibility and citation/table metadata preservation;
- scope grep proves hierarchy/drill-down work remains deferred to Phase 22.

## RESEARCH COMPLETE
