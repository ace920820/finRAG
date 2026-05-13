---
phase: 03-agent-workflow-and-sse-query-api
plan: 01
subsystem: agent-workflow
tags: [agent, query-rewrite, intent, generation, citations]
key-files:
  - backend/app/core/agent/query_analysis.py
  - backend/app/core/agent/prompts.py
  - backend/app/core/agent/generator.py
  - backend/app/core/agent/workflow.py
  - backend/app/core/providers/rerank.py
  - backend/tests/test_query_analysis.py
  - backend/tests/test_agent_workflow.py
metrics:
  tests: 6 passed
---

# Plan 03-01 Summary: Agent Workflow Core

## Completed

- Added deterministic query rewrite and intent classification for factual, analytical, and reasoning queries.
- Added Qwen Plus-oriented prompt assembly using top reranked evidence.
- Added deterministic mock answer generation with frontend-clickable citation spans.
- Updated the text provider seam so live Qwen Plus remains config-driven while tests stay offline.
- Added `QueryWorkflow` orchestration across query analysis, retrieval, rerank, generation, and citation metadata.
- Added focused workflow and query analysis tests.

## Deviations

- Provider-level streaming is intentionally not implemented; the SSE layer chunks complete generated text for MVP stability.

## Self-Check

PASSED — `cd backend && python3 -m pytest tests/test_query_analysis.py tests/test_agent_workflow.py`.
