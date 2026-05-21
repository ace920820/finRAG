# Quick Task 260521-meg Plan

## Task
Fix Phase 19/20 code review findings for retrieval plan propagation, evidence packing, and cascade trace.

## Scope
- Pass structured retrieval plan through `QueryWorkflow.run()` to retriever.
- Make `build_evidence_pack()` tolerant of missing `citation_id`.
- Align retrieval cascade trace order with actual execution order and mark metadata filters as post-recall.
- Make `final_evidence` trace reflect EvidencePack compression counts.
- Keep debug/prompts interface cleanup out of this hotfix.

## Verification
- `cd backend && pytest tests/test_agent_workflow.py tests/test_context_builder.py tests/test_hybrid_retrieval.py tests/test_query_api.py tests/test_debug_retrieval.py -q`
- `cd backend && pytest -q`
