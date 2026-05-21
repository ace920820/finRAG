---
phase: 20-evidence-compression-and-context-builder
plan: 01
subsystem: agent
tags:
  - evidence-compression
  - context-builder
  - citations
key-files:
  - backend/app/core/agent/context_builder.py
  - backend/app/core/agent/generator.py
  - backend/app/core/agent/prompts.py
  - backend/app/core/agent/workflow.py
  - backend/app/api/query.py
  - backend/tests/test_context_builder.py
  - backend/tests/test_agent_workflow.py
  - backend/tests/test_query_api.py
metrics:
  focused_tests: "14 passed"
  full_backend_tests: "100 passed"
---

# Phase 20 Summary

## Outcome

Implemented deterministic evidence compression between rerank and generation while preserving table-fact data, citation IDs, and existing query SSE behavior.

## Changes

- Added `build_evidence_pack()` with deterministic evidence packing, deduplication, and compact text handling.
- Added `EvidencePack` / `EvidencePackItem` models in the context builder module.
- Preserved table fact fields including value, unit, currency, period, table, page, and source metadata.
- Integrated evidence packs into:
  - `AnswerGenerator.generate()`
  - `build_generation_prompt()`
  - streaming `/api/query`
  - `QueryWorkflow.run()`
- Preserved legacy `AnswerGenerator.generate(query, intent, evidence)` compatibility.
- Added regression tests for table facts, dedupe, text compaction, prompt compaction, workflow, and query API compatibility.

## Verification

- `python3 -m pytest backend/tests/test_context_builder.py backend/tests/test_agent_workflow.py backend/tests/test_query_api.py -q`
  - Result: 14 passed, 5 warnings
- `cd backend && python3 -m pytest -q`
  - Result: 100 passed, 5 warnings
- `rg "retrieval_planner|iterative|parent_id|chunk_level|drill" backend/app backend/tests`
  - Result: no matches

## Deviations

- The evidence pack models live in `backend/app/core/agent/context_builder.py` rather than `schemas.py` because they are internal agent-generation context and are not currently API response contracts.

## Self-Check

PASSED

- EVIDENCE-01: generation uses compact evidence packs.
- EVIDENCE-02: table facts preserve required numeric/source metadata.
- EVIDENCE-03: citations remain source-grounded and accurate.
- EVIDENCE-04: tests cover text evidence, table facts, duplicate evidence, and citation preservation.
