# Phase 18: Knowledge Routing And Metadata Pre-filtering - Research

**Researched:** 2026-05-21 [VERIFIED: environment date]
**Domain:** Retrieval routing, metadata pre-filtering, debug observability [VERIFIED: .planning/ROADMAP.md]
**Confidence:** HIGH for integration shape; MEDIUM for exact route/filter shape until planner locks task decomposition [VERIFIED: codebase inspection]

<user_constraints>
## User Constraints / Locked Decisions

- Phase 18 must consume the structured `RetrievalPlan` produced in Phase 17. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- Route selection must be deterministic and rule-based. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- `table_fact_first` is the primary path for metric/numeric queries with both company and metric. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- Metadata pre-filters should be strong by default, but they must relax and fall back if they over-constrain the candidate set. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- `/api/debug/retrieval` is the first place routing/filter observability should appear. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- Normal `/api/query` SSE must remain unchanged in Phase 18 except for internal consumption of the plan. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- `HybridRetriever.retrieve(query: str)` compatibility must be preserved. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- Existing table-aware numeric QA and general text RAG behavior must remain green. [VERIFIED: .planning/REQUIREMENTS.md, .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description |
|----|-------------|
| ROUTE-01 | Queries route to specialized retrieval strategies such as table-fact-first, financial-report section search, research-report analysis, and general hybrid fallback. |
| ROUTE-02 | Retrieval applies metadata pre-filters before expensive recall when the query plan identifies company, document type, period/date, chunk type, metric, or collection constraints. |
| ROUTE-03 | Retrieval/debug outputs expose route choice, applied filters, and candidate counts before and after filtering. |
| ROUTE-04 | Routing and filtering preserve existing table-aware numeric QA behavior and existing general text RAG behavior. |

</phase_requirements>

<codebase_findings>
## Codebase Findings

### Existing retrieval flow

- `backend/app/api/query.py` and `backend/app/core/agent/workflow.py` both call `HybridRetriever.retrieve()` with a string query today. [VERIFIED: backend/app/api/query.py, backend/app/core/agent/workflow.py]
- `HybridRetriever.retrieve()` currently performs BM25, vector, and supplemental/table-fact hit collection, then RRF fusion. [VERIFIED: backend/app/core/retrieval/hybrid.py]
- Table facts already have a dedicated query path via `query_table_facts()` and `is_table_metric_query()`. [VERIFIED: backend/app/core/retrieval/hybrid.py, backend/app/core/retrieval/table_facts.py]
- `RerankService` already applies strong table-fact period compatibility and revenue/net-income boosts, so Phase 18 should not reimplement ranking logic in the routing layer. [VERIFIED: backend/app/core/retrieval/rerank_service.py]

### Existing debug surface

- `/api/debug/retrieval` already returns retrieval and rerank sections and is the right place to expose routing metadata first. [VERIFIED: backend/app/api/debug.py, backend/tests/test_debug_retrieval.py]
- Current debug tests only assert retrieval/rerank presence and candidate lists, so Phase 18 can extend the debug response shape without breaking the endpoint contract if fields remain additive. [VERIFIED: backend/tests/test_debug_retrieval.py]

### Existing query-plan source

- Phase 17 provides `RetrievalPlan` with entities, metrics, time range, retrieval strategy, filters, and signals, and its tests already prove compatibility with existing SSE order. [VERIFIED: .planning/phases/17-structured-query-understanding-and-retrieval-plan/17-01-SUMMARY.md]
- `QueryRewriteEvent.plan` is available on the workflow side, so `QueryWorkflow` and the API route can pass the plan down without changing the public query entry point. [VERIFIED: backend/app/models/events.py, backend/app/core/agent/workflow.py, backend/app/api/query.py]

### Relevant existing tests

- `backend/tests/test_hybrid_retrieval.py` already proves numeric table facts can dominate rerank for NVIDIA revenue, and that table facts are suppressed on period mismatch. [VERIFIED: backend/tests/test_hybrid_retrieval.py]
- `backend/tests/test_debug_retrieval.py` already covers the debug endpoint structure. [VERIFIED: backend/tests/test_debug_retrieval.py]
- `backend/tests/test_query_api.py` already proves `/api/query` SSE event order and the table-fact path remain stable. [VERIFIED: backend/tests/test_query_api.py]

</codebase_findings>

<implementation_options>
## Implementation Options

### Option A: Add a small router + filters layer in front of HybridRetriever

**Shape:** create `backend/app/core/retrieval/router.py` and `backend/app/core/retrieval/filters.py`, then let `HybridRetriever.retrieve()` accept an optional `RetrievalPlan`.

**Pros:**
- Keeps routing and filtering separate from BM25/vector internals.
- Matches the phase boundary cleanly.
- Preserves current retrieval stack and tests.

**Cons:**
- Requires a small API extension to retrieve optional debug metadata.
- Needs careful fallback handling so filters do not empty the candidate set.

### Option B: Fold routing/filtering directly into HybridRetriever

**Shape:** add route and filter decisions inside `HybridRetriever.retrieve()` and store debug details on the result object.

**Pros:**
- Fewer new files.
- Easier to wire into existing retrieval flow quickly.

**Cons:**
- Makes HybridRetriever do more than one job.
- Harder to keep route selection independent from candidate collection.
- More likely to blur Phase 18 with Phase 19 tracing later.

### Option C: Pre-filter inside BM25/vector stores

**Shape:** alter BM25/vector search functions to take route/filter constraints.

**Pros:**
- Filters are physically near recall.

**Cons:**
- Too invasive for Phase 18.
- Risks breaking existing retrieval behavior and table-fact matching.
- Not necessary because the phase only needs route/filter decisions, not a new search engine.

</implementation_options>

<recommendation>
## Recommendation

Use Option A.

The safest Phase 18 shape is:

1. Add a small routing module that maps `RetrievalPlan` to one of four routes:
   - `table_fact_first`
   - `financial_report_first`
   - `research_report_analysis`
   - `general_hybrid`
2. Add a metadata filter helper that can construct and relax constraints for company, doc_type, chunk_type, metric, collection, and period/date.
3. Extend `HybridRetriever.retrieve()` with an optional `plan: RetrievalPlan | None = None`.
4. Keep the string-only path working exactly as today.
5. Expose route/filter metadata first in `/api/debug/retrieval`, not in the main SSE query stream.

This keeps Phase 18 narrow, lets Phase 19 add stage tracing cleanly, and preserves table-aware QA stability.

</recommendation>

<risks>
## Risks

- Overly strict filters could drop candidate counts to zero on noisy queries unless fallback relaxation is implemented.
- A route decision based only on company + metric may over-prioritize table facts for analytical queries that also mention numbers; the router should prefer `research_report_analysis` whenever causal/risk/trend signals dominate. [VERIFIED: .planning/phases/18-knowledge-routing-and-metadata-pre-filtering/18-CONTEXT.md]
- Debug metadata must stay additive so older clients can ignore it safely.
- The existing persisted vector index may mismatch the active embedding provider in some environments, so tests should avoid coupling route/filter assertions to a live vector recall assumption. [VERIFIED: backend/tests/test_query_api.py, current workspace state]

</risks>

<planning_notes>
## Planning Notes

- Do not change the meaning of `retrieval_complete` in the main SSE path in Phase 18.
- Do not push stage-trace concepts into Phase 18; route/filter counts are enough.
- Keep table fact handling aligned with `table_facts.py` and `RerankService` so numeric answers stay stable.
- Prefer additive debug fields and optional plan parameters over breaking signatures.

</planning_notes>

---

*Phase: 18-knowledge-routing-and-metadata-pre-filtering*
*Research completed: 2026-05-21*

