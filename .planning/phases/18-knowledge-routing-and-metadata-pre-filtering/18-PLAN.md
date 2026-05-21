---
phase: 18-knowledge-routing-and-metadata-pre-filtering
plan: 01
type: execute
wave: 1
depends_on: [17-01]
files_modified:
  - backend/app/core/retrieval/router.py
  - backend/app/core/retrieval/filters.py
  - backend/app/core/retrieval/hybrid.py
  - backend/app/api/debug.py
  - backend/app/models/events.py
  - backend/tests/test_hybrid_retrieval.py
  - backend/tests/test_debug_retrieval.py
  - backend/tests/test_query_api.py
autonomous: true
requirements:
  - ROUTE-01
  - ROUTE-02
  - ROUTE-03
  - ROUTE-04
user_setup: []
must_haves:
  truths:
    - "Queries route deterministically to table_fact_first, financial_report_first, research_report_analysis, or general_hybrid based on the Phase 17 retrieval plan."
    - "HybridRetriever.retrieve(query: str) remains backward compatible."
    - "Metadata pre-filters use conservative priority and relax automatically when the candidate set is too narrow."
    - "Debug retrieval exposes route choice, filters, candidate counts before/after filtering, and fallback reasons."
    - "Normal /api/query SSE event order remains unchanged."
    - "Existing table-aware numeric QA still returns the NVIDIA Q3 revenue table fact and preserves general text RAG behavior."
  artifacts:
    - path: "backend/app/core/retrieval/router.py"
      provides: "deterministic RetrievalPlan -> route decision helper"
      contains: "def choose_route"
    - path: "backend/app/core/retrieval/filters.py"
      provides: "metadata filter construction, application, and relaxation helpers"
      contains: "def apply_metadata_filters"
    - path: "backend/app/core/retrieval/hybrid.py"
      provides: "optional plan-aware retrieval entrypoint and debug metadata propagation"
      contains: "def retrieve"
    - path: "backend/app/api/debug.py"
      provides: "debug response route/filter observability"
      contains: "route"
    - path: "backend/tests/test_hybrid_retrieval.py"
      provides: "route/filter regression coverage for factual, analytical, and table-fact queries"
      contains: "test_"
    - path: "backend/tests/test_debug_retrieval.py"
      provides: "debug response route/filter assertions"
      contains: "route"
    - path: "backend/tests/test_query_api.py"
      provides: "SSE compatibility regression coverage"
      contains: "test_query_endpoint"
  key_links:
    - from: "backend/app/core/agent/query_analysis.py"
      to: "backend/app/core/retrieval/router.py"
      via: "rewrite.plan"
      pattern: "RetrievalPlan"
    - from: "backend/app/core/retrieval/router.py"
      to: "backend/app/core/retrieval/filters.py"
      via: "route-specific filter presets"
      pattern: "metadata"
    - from: "backend/app/core/retrieval/filters.py"
      to: "backend/app/core/retrieval/hybrid.py"
      via: "filtered candidate sets and fallback reason"
      pattern: "fallback"
    - from: "backend/app/api/debug.py"
      to: "debug retrieval response"
      via: "route/filter metadata fields"
      pattern: "route"
---

<objective>
Introduce plan-aware routing and metadata pre-filtering on top of the existing retrieval stack while preserving the current SSE query contract and existing table-aware QA behavior.

Purpose: Make the retrieval entrypoint and debug surface aware of `RetrievalPlan` so later phases can build on the same route/filter API without changing it again.
Output: deterministic route selection, metadata filter construction and relaxation, plan-aware hybrid retrieval plumbing, debug observability, and regression tests for route/filter behavior.
</objective>

<execution_context>
@/Users/jamiezhao/.codex/get-shit-done/workflows/execute-phase.md
@/Users/jamiezhao/.codex/get-shit-done/templates/summary.md
@/Users/jamiezhao/.codex/skills/karpathy-guidelines/SKILL.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/REQUIREMENTS.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md
@.planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-RESEARCH.md
@AGENTS.md
@backend/app/core/agent/query_analysis.py
@backend/app/core/retrieval/hybrid.py
@backend/app/core/retrieval/table_facts.py
@backend/app/api/debug.py
@backend/tests/test_debug_retrieval.py
@backend/tests/test_hybrid_retrieval.py
@backend/tests/test_query_api.py

<interfaces>
Existing public contracts that must remain valid:

```python
def retrieve(query: str) -> HybridRetrievalResult
```

```python
class HybridRetrievalResult:
    bm25_results: list[RetrievalResultItem]
    vector_results: list[RetrievalResultItem]
    fused_top20: list[RetrievalResultItem]
    bm25_error: Optional[str] = None
    vector_error: Optional[str] = None
```

```python
class DebugRetrievalResponse(BaseModel):
    retrieval_complete: RetrievalCompleteEvent
    rerank_complete: RerankCompleteEvent
    degraded: bool = False
    fallback_reason: Optional[str] = None
```

</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add failing route/filter observability tests</name>
  <files>backend/tests/test_hybrid_retrieval.py, backend/tests/test_debug_retrieval.py, backend/tests/test_query_api.py</files>
  <read_first>
    - .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md
    - .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-RESEARCH.md
    - backend/tests/test_hybrid_retrieval.py
    - backend/tests/test_debug_retrieval.py
    - backend/tests/test_query_api.py
    - backend/app/core/retrieval/hybrid.py
    - backend/app/api/debug.py
    - backend/app/core/agent/query_analysis.py
  </read_first>
  <action>
    Add tests that lock the Phase 18 behavior before production changes:
    - a numeric NVIDIA revenue query should route to `table_fact_first` and still return the existing table fact path;
    - a CATL / 宁德时代 risk query should route to `research_report_analysis`;
    - a report/filing-style company query should route to `financial_report_first` when it has company + time but no clear table-fact lookup;
    - the debug retrieval response should expose route choice, filters, candidate counts before/after filtering, and fallback reason fields;
    - the normal `/api/query` SSE contract should remain unchanged;
    - fallback relaxation should be observable when a query is too narrow for strict filters.

    Keep assertions concrete: route names, filter payload fields, counts, and fallback reasons. Do not assert Phase 19 stage trace fields.
  </action>
  <verify>
    <automated>cd backend && pytest tests/test_hybrid_retrieval.py tests/test_debug_retrieval.py tests/test_query_api.py -q</automated>
  </verify>
  <acceptance_criteria>
    - `rg "route|filters|candidate" backend/tests/test_debug_retrieval.py` returns matches for the new assertions.
    - `rg "table_fact_first|research_report_analysis|financial_report_first" backend/tests/test_hybrid_retrieval.py` returns matches for the new route assertions.
    - `rg "fallback" backend/tests/test_hybrid_retrieval.py backend/tests/test_debug_retrieval.py` returns matches for relaxation coverage.
    - Existing query SSE event-order assertions remain present.
    - The first run may fail before implementation, but failures must be from missing route/filter behavior, not syntax errors.
  </acceptance_criteria>
  <done>Wave 0 encodes route and filter observability requirements before implementation.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Add routing and metadata filter helpers with optional plan-aware retrieval plumbing</name>
  <files>backend/app/core/retrieval/router.py, backend/app/core/retrieval/filters.py, backend/app/core/retrieval/hybrid.py, backend/app/api/debug.py, backend/app/models/events.py, backend/tests/test_hybrid_retrieval.py, backend/tests/test_debug_retrieval.py</files>
  <read_first>
    - .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md
    - .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-RESEARCH.md
    - backend/app/core/retrieval/hybrid.py
    - backend/app/core/retrieval/table_facts.py
    - backend/app/api/debug.py
    - backend/app/models/events.py
    - backend/tests/test_hybrid_retrieval.py
    - backend/tests/test_debug_retrieval.py
  </read_first>
  <action>
    Implement a small router module that maps `RetrievalPlan` to one of the four phase routes based on company, metric, time range, and task type.

    Implement a filters module that can:
    - build metadata constraints from plan fields,
    - apply them conservatively to candidate sets,
    - report counts before and after filtering,
    - relax filters automatically when the candidate set becomes too narrow,
    - return a fallback reason / relaxed-filter note.

    Extend `HybridRetriever.retrieve()` in the smallest way possible so it can accept an optional plan while preserving string-only compatibility. Keep table-fact behavior aligned with Phase 16 and do not change BM25/vector internals unnecessarily.

    Extend `/api/debug/retrieval` to include route/filter metadata using additive fields only.
  </action>
  <verify>
    <automated>cd backend && pytest tests/test_hybrid_retrieval.py tests/test_debug_retrieval.py tests/test_query_api.py -q</automated>
  </verify>
  <acceptance_criteria>
    - `rg "def choose_route|def apply_metadata_filters" backend/app/core/retrieval` returns matches.
    - `rg "route" backend/app/api/debug.py` returns a match for the new observability fields.
    - `rg "RetrievalPlan|plan" backend/app/core/retrieval/hybrid.py` returns a match for plan-aware plumbing.
    - String-only retrieval callers still work.
    - Table-aware numeric QA still passes its existing regression tests.
  </acceptance_criteria>
  <done>Route selection and metadata filtering exist as plan-aware helpers without breaking current retrieval callers.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Validate debug and retrieval regressions after routing integration</name>
  <files>backend/tests/test_hybrid_retrieval.py, backend/tests/test_debug_retrieval.py, backend/tests/test_query_api.py</files>
  <read_first>
    - .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md
    - .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-RESEARCH.md
    - .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-VALIDATION.md
    - backend/tests/test_hybrid_retrieval.py
    - backend/tests/test_debug_retrieval.py
    - backend/tests/test_query_api.py
    - backend/app/core/retrieval/hybrid.py
    - backend/app/api/debug.py
  </read_first>
  <action>
    Tighten regression coverage so the phase proves:
    - research/analysis queries route away from table-fact-first when narrative evidence is needed;
    - metadata relaxation is visible in the debug response;
    - existing SSE order and answer flow remain unchanged;
    - table-aware numeric QA stays green for NVIDIA revenue;
    - general text RAG behavior still returns bm25/vector/fused results on normal retrieval queries.

    Keep the verification focused on behavior that Phase 18 owns. Do not add cascade trace fields or evidence compression.
  </action>
  <verify>
    <automated>cd backend && pytest tests/test_hybrid_retrieval.py tests/test_debug_retrieval.py tests/test_query_api.py -q</automated>
  </verify>
  <acceptance_criteria>
    - The route assertions, debug observability assertions, and SSE compatibility checks all pass.
    - `HybridRetriever` still supports string-only callers.
    - Existing table-fact and general retrieval regressions remain green.
  </acceptance_criteria>
  <done>Phase 18 behavior is validated without introducing Phase 19 trace semantics.</done>
</task>

<threat_model>
## Threat Model

- **[high] Route/filter tampering via query text** — Treat route and filter fields as extracted metadata only; never execute them as code or eval-like expressions.
- **[high] Over-filtering leading to silent empty retrieval** — Must relax filters and emit fallback reason instead of returning empty candidates too early.
- **[medium] Debug leakage of internal metadata** — Keep observability additive and avoid exposing secrets or provider internals.
- **[medium] Regression of table-aware numeric QA** — Preserve the specialized table-fact path and current rerank behavior for financial metrics.
- **[medium] Contract drift in `/api/query` SSE** — Do not alter event order or require frontend changes in this phase.
</threat_model>

<verification>
## Verification

- `cd backend && pytest tests/test_hybrid_retrieval.py tests/test_debug_retrieval.py tests/test_query_api.py -q`
- `cd backend && pytest -q` before phase completion
- Spot-check debug response payloads for route/filter metadata on a representative numeric and analytic query
</verification>

<success_criteria>
- Queries route deterministically to table_fact_first, financial_report_first, research_report_analysis, or general_hybrid.
- Metadata pre-filters shrink candidate sets before expensive recall and relax automatically when too narrow.
- Debug retrieval exposes route choice, filters, candidate counts before/after filtering, and fallback reasons.
- Existing table-aware numeric QA and general text RAG behavior remain green.
- Normal `/api/query` SSE contract remains unchanged.
</success_criteria>
