---
phase: 17-structured-query-understanding-and-retrieval-plan
plan: 01
subsystem: api
tags: [rag, query-planning, pydantic, sse, testing, flashtext, dateparser]
requires:
  - phase: 16
    provides: table-aware numeric QA and shared alias behavior
provides:
  - typed retrieval plan contract for query understanding
  - optional QueryRewriteEvent.plan serialization
  - ontology matcher abstraction with deterministic fallback
  - shared entity/metric alias source for query analysis and table facts
affects: [Phase 18 routing/filtering, Phase 19 cascade trace, query SSE consumers]
tech-stack:
  added: [flashtext-i18n, dateparser]
  patterns: [typed retrieval plan, matcher abstraction, deterministic rule-based parsing]
key-files:
  created: [backend/app/core/agent/query_ontology.py]
  modified:
    - backend/app/core/agent/query_analysis.py
    - backend/app/core/retrieval/table_facts.py
    - backend/app/models/events.py
    - backend/app/models/schemas.py
    - backend/tests/test_query_analysis.py
    - backend/tests/test_query_api.py
    - backend/tests/test_sse_formatter.py
    - backend/requirements.txt
key-decisions:
  - "Keep analyze_query(query) returning exactly (QueryRewriteEvent, IntentDetectedEvent) while attaching plan metadata to the rewrite event."
  - "Use a deterministic rule-based parser with a FlashText-backed matcher when available and a stdlib fallback when not."
  - "Centralize company and metric aliases in query_ontology.py and import them from table_facts to avoid drift."
patterns-established:
  - "Pattern 1: QueryRewriteEvent carries optional RetrievalPlan without changing SSE event order."
  - "Pattern 2: Query analysis builds a typed plan from normalized text while preserving original user input."
requirements-completed: [QUERY-01, QUERY-02, QUERY-03]
duration: 33min
completed: 2026-05-21
---

# Phase 17: Structured Query Understanding And Retrieval Plan Summary

Structured query planning is now exposed on the existing rewrite event without changing the query workflow contract.

## Performance

- **Duration:** 33 min
- **Started:** 2026-05-21T04:16:00Z
- **Completed:** 2026-05-21T04:49:39Z
- **Tasks:** 1
- **Files modified:** 8

## Accomplishments
- Added typed retrieval plan models and `QueryRewriteEvent.plan`.
- Built a deterministic query planner with entity, metric, time, task type, strategy, filters, and signals.
- Centralized alias data and preserved the existing SSE event order.
- Added regression coverage for NVIDIA, 贵州茅台, 宁德时代, 台积电, and ordinary-date fallback behavior.

## Task Commits

1. **Task 1: Add structured query plan contracts and regressions** - not committed separately in this session

## Files Created/Modified
- `backend/app/core/agent/query_ontology.py` - shared ontology, normalization, and matcher fallback
- `backend/app/core/agent/query_analysis.py` - structured plan builder and backward-compatible rewrite boundary
- `backend/app/core/retrieval/table_facts.py` - imports shared alias constants
- `backend/app/models/events.py` - optional plan on query rewrite events
- `backend/app/models/schemas.py` - retrieval plan schema types
- `backend/tests/test_query_analysis.py` - structured parser regressions
- `backend/tests/test_query_api.py` - SSE plan exposure regression
- `backend/tests/test_sse_formatter.py` - plan serialization coverage
- `backend/requirements.txt` - `flashtext-i18n` and `dateparser` pins

## Decisions Made
- Kept Phase 17 strictly contract-preserving.
- Used a local matcher abstraction instead of introducing any model-based planner.
- Reused the table-fact alias vocabulary as the shared metric/entity source.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The environment lacked installed `pytest`, so validation used `python3 -m pytest`.
- The persisted vector index in the workspace did not match the active embedding provider, so the SSE regression test was kept focused on plan exposure and event order rather than vector recall.

## Next Phase Readiness

Phase 18 can consume `RetrievalPlan` for routing and metadata filtering without breaking existing query rewrite or SSE consumers.

