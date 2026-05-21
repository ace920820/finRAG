# Phase 21: Agentic Iterative Retrieval Demo Mode - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning
**Mode:** Discuss fallback defaults applied because interactive selection was unavailable

<domain>
## Phase Boundary

Phase 21 adds a lightweight, demo-friendly iterative retrieval mode for complex financial analytical and reasoning questions.

This phase should show retrieval as a purposeful process: the system identifies evidence needs, issues a small number of targeted retrieval steps, records each step's purpose/query/route/filter/evidence, and then uses the existing rerank/context-builder/generation path.

This phase must not change simple factual/table-fact lookup behavior. It also must not introduce hierarchy/drill-down retrieval, new corpus chunking, frontend redesign, or a full autonomous agent loop.

</domain>

<decisions>
## Implementation Decisions

### Trigger Policy

- **I-01:** Enable iterative retrieval only for analytical/reasoning questions where the Phase 17 plan indicates `risk_analysis`, `causal_analysis`, `trend_analysis`, or `comparison`.
- **I-02:** Simple factual and metric lookup queries must stay on the single-pass cascade path.
- **I-03:** Table-fact-first numeric QA must remain single-pass unless a later phase explicitly asks for multi-step numeric verification.

### Step Count And Planning Style

- **I-04:** Use a maximum of 3 retrieval steps.
- **I-05:** Step planning should be deterministic and rule-based under tests; no LLM call is required to create retrieval steps.
- **I-06:** Recommended step purposes:
  - `background_facts` — establish company/metric/event context.
  - `risk_or_driver_evidence` — collect risk, causal, trend, or comparison evidence.
  - `cross_check` — gather confirming or contrasting evidence when useful.
- **I-07:** The planner may produce fewer than 3 steps when the query is simple or the plan lacks enough signals.

### Step Execution

- **I-08:** Each step should reuse the existing `HybridRetriever.retrieve(query, plan=...)`, Phase 18 routing/filtering, Phase 19 cascade trace, and Phase 20 context builder.
- **I-09:** Each step records:
  - purpose
  - generated retrieval query
  - route
  - applied filters
  - selected evidence IDs or top evidence summaries
  - fallback/degraded metadata
- **I-10:** Step evidence should be merged deterministically and deduped before final rerank/context building.

### Observability

- **I-11:** Expose iterative retrieval through additive fields on existing payloads and debug responses.
- **I-12:** Do not add new SSE event names in Phase 21.
- **I-13:** Keep Phase 19 `cascade_trace` intact; iterative steps should be a separate optional structure, not overloaded into cascade stage names.
- **I-14:** `/api/debug/retrieval` or a debug-adjacent surface should show the clearest step trace first.

### Fallback Behavior

- **I-15:** If step planning fails, step execution fails, or evidence quality is insufficient, degrade to the normal single-pass cascade.
- **I-16:** Fallback must be visible through a reason such as `iterative_planning_failed`, `iterative_step_failed`, or `iterative_no_evidence`.
- **I-17:** Degraded iterative mode must still return the normal SSE sequence and answer flow.

### Compatibility

- **I-18:** Existing `/api/query` event names and order remain unchanged.
- **I-19:** Existing table-aware numeric QA and citation metadata tests must remain green.
- **I-20:** Phase 20 evidence packs remain the final generation input; iterative retrieval only changes how candidate evidence is gathered for analytical/reasoning questions.

</decisions>

<specifics>
## Specific Ideas

- Use a small `retrieval_planner.py` module only if planning logic grows beyond a helper function; otherwise keep the first implementation modest.
- Use existing `RetrievalPlan.task_type` and `intent` to decide iterative eligibility.
- Candidate query templates can reuse Phase 17 expansions and sub-queries:
  - original query + "相关事实依据"
  - entity aliases + risk/driver terms
  - comparison/cross-check wording when task type is `comparison` or `causal_analysis`
- Representative tests should include:
  - 宁德时代 risk query produces iterative steps.
  - A reasoning/causal query produces 2-3 purposeful steps.
  - NVIDIA revenue lookup remains single-pass and table-fact-backed.
  - Iterative failure falls back to single-pass with visible reason.

</specifics>

<deferred>
## Deferred Ideas

- Full autonomous agent planning loop with LLM-generated retrieval strategies — deferred.
- New frontend visualization for step traces — deferred unless explicitly requested.
- Hierarchical drill-down retrieval — Phase 22.
- Knowledge graph or graph traversal planning — future milestone.

</deferred>

---

*Phase: 21-agentic-iterative-retrieval-demo-mode*
*Context gathered: 2026-05-21*
