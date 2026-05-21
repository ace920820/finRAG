---
phase: 21-agentic-iterative-retrieval-demo-mode
plan: 01
subsystem: retrieval
tags:
  - iterative-retrieval
  - retrieval-trace
  - sse
  - debug
requires:
  - phase: 20-evidence-compression-and-context-builder
    provides: compact evidence packs for final generation input
provides:
  - deterministic iterative retrieval planner for analytical/reasoning queries
  - additive iterative trace fields on retrieval/debug payloads
  - fallback to single-pass retrieval for failures and factual/table lookups
affects:
  - query-api
  - debug-retrieval
  - agent-workflow
tech-stack:
  added: []
  patterns:
    - deterministic rule-based retrieval planning
    - shared retrieval/rerank pipeline helper
key-files:
  created:
    - backend/app/core/agent/retrieval_planner.py
    - backend/tests/test_retrieval_planner.py
  modified:
    - backend/app/core/agent/workflow.py
    - backend/app/api/query.py
    - backend/app/api/debug.py
    - backend/app/models/schemas.py
    - backend/app/models/events.py
    - backend/tests/test_agent_workflow.py
    - backend/tests/test_query_api.py
    - backend/tests/test_debug_retrieval.py
key-decisions:
  - "Iterative retrieval is gated by RetrievalPlan task_type and excludes table_fact_first/metric_lookup."
  - "Iterative trace is separate from cascade_trace and exposed through existing retrieval_complete/debug payloads only."
patterns-established:
  - "Use run_retrieval_pipeline() for workflow, SSE, and debug retrieval orchestration parity."
  - "Fallback reasons use iterative_planning_failed, iterative_step_failed, or iterative_no_evidence."
requirements-completed:
  - ITER-01
  - ITER-02
  - ITER-03
  - ITER-04
duration: ~70min
completed: 2026-05-21T08:47:51Z
---

# Phase 21: Agentic Iterative Retrieval Demo Mode Summary

**Rule-based multi-step retrieval trace for analytical financial questions with single-pass fallback for factual/table QA**

## Performance

- **Duration:** ~70 min
- **Started:** 2026-05-21T08:37:40Z
- **Completed:** 2026-05-21T08:47:51Z
- **Tasks:** 5
- **Files modified:** 12

## Accomplishments

- Added deterministic iterative retrieval planning for `risk_analysis`, `causal_analysis`, `trend_analysis`, and `comparison`.
- Added `IterativeRetrievalTrace` / `IterativeRetrievalStep` schemas and additive `retrieval_complete.iterative_trace`.
- Centralized workflow, SSE query, and debug retrieval through `run_retrieval_pipeline()`.
- Implemented fallback to the normal single-pass cascade for planning failure, step failure, and no iterative evidence.
- Preserved SSE event names/order and table-fact numeric QA behavior.

## Task Commits

Implementation committed as a single Phase 21 execution changeset.

## Files Created/Modified

- `backend/app/core/agent/retrieval_planner.py` - deterministic eligibility and step planning.
- `backend/app/core/agent/workflow.py` - shared retrieval/rerank/evidence pipeline with iterative candidate gathering and fallback.
- `backend/app/api/query.py` - reuses shared pipeline while preserving existing SSE events.
- `backend/app/api/debug.py` - exposes top-level and retrieval payload iterative traces.
- `backend/app/models/schemas.py` - iterative trace schema models.
- `backend/app/models/events.py` - additive `iterative_trace` field on retrieval event payload.
- `backend/tests/test_retrieval_planner.py` - planner eligibility and deterministic step coverage.
- `backend/tests/test_agent_workflow.py` - workflow iterative, fallback, and single-pass regression coverage.
- `backend/tests/test_query_api.py` - SSE additive trace and table-fact regression coverage.
- `backend/tests/test_debug_retrieval.py` - debug iterative trace coverage.

## Decisions Made

- Kept iterative planning deterministic and local; no LLM planner loop.
- Kept `cascade_trace` unchanged and separate from `iterative_trace`.
- Reused the existing final rerank and Phase 20 evidence pack path after multi-step candidate collection.
- Omitted iterative trace for ineligible factual/table queries to keep simple payloads minimal.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used module-invoked pytest command**
- **Found during:** Task 1 verification
- **Issue:** `pytest` was not on PATH in this shell, so the planned command failed with `command not found`.
- **Fix:** Used `python3 -m pytest` for all verification commands.
- **Files modified:** None.
- **Verification:** Focused and full backend suites passed.
- **Committed in:** pending final commit.

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** No implementation scope change; only command invocation changed.

## Issues Encountered

- One initial comparison-query planner test used wording that the existing query analyzer classified as table-fact-first metric lookup. The test query was adjusted to include explicit comparison wording rather than expanding analyzer behavior outside Phase 21 scope.

## Verification

- `cd backend && python3 -m pytest tests/test_retrieval_planner.py -q`
  - Result: 5 passed, 5 warnings
- `cd backend && python3 -m pytest tests/test_retrieval_planner.py tests/test_agent_workflow.py tests/test_query_api.py tests/test_debug_retrieval.py -q`
  - Result: 20 passed, 5 warnings
- `cd backend && python3 -m pytest -q`
  - Result: 111 passed, 5 warnings
- `rg "parent_id|chunk_level|section_path|child relationship|drill_down|hierarchical" backend/app backend/tests`
  - Result: no matches

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 22 can build hierarchy/drill-down retrieval on top of the existing plan, route/filter, cascade trace, evidence pack, and iterative trace layers. No blockers.

---
*Phase: 21-agentic-iterative-retrieval-demo-mode*
*Completed: 2026-05-21*
