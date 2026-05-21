# Quick Task 260521-meg Summary

## Completed

Fixed Phase 19/20 code review findings around retrieval path consistency and cascade trace observability.

## Changes

- Passed `rewrite.plan` from `QueryWorkflow.run()` into `retriever.retrieve()` and carried cascade trace through workflow result events.
- Made `build_evidence_pack()` tolerate objects without `citation_id` by defaulting to `0`.
- Reordered retrieval cascade trace to match actual execution: `query_plan -> coarse_recall -> metadata_filter -> fusion`.
- Marked metadata filtering as `metadata_post_recall_filter` with `applied_at: post_recall` metadata.
- Made `final_evidence` trace report EvidencePack compression counts instead of duplicating rerank counts.
- Updated query, debug, workflow, retrieval, and context builder regression tests.

## Verification

- `cd backend && python3 -m pytest tests/test_agent_workflow.py tests/test_context_builder.py tests/test_hybrid_retrieval.py tests/test_query_api.py tests/test_debug_retrieval.py -q` -> 26 passed.
- `cd backend && python3 -m pytest -q` -> 102 passed.

## Commit

- `98a627c fix: align retrieval trace and evidence packing paths`
