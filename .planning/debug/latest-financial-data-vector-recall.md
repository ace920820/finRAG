---
status: resolved
trigger: "Investigate and fix FinRAG retrieval issue: latest financial data query returns older annual revenue and Vector semantic recall is empty in UI."
created: 2026-05-14T00:00:00+08:00
updated: 2026-05-14T00:06:00+08:00
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: Fix applied; needs user verification in the real UI workflow.
test: Ask user to rerun the two Moutai queries and inspect Vector panel degraded state.
expecting: Latest query answers from 2026Q1 table_fact; Vector panel shows dimension mismatch/degraded message if index is incompatible.
next_action: wait for human verification

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: For queries like “贵州茅台最新的营收数据” the system should prefer the latest available quarterly/period financial fact (e.g. 2026Q1 if available) instead of older FY2024 annual revenue. Vector semantic recall should either show semantic results when the vector index is available or clearly expose an error/degraded state instead of silently empty.
actual: User screenshot shows explicit query “2026 第一季度贵州茅台营业收入” returns 2026Q1 values, but query “贵州茅台最新的营收数据” answers 94,526,738,836.41 RMB for 2024 annual revenue. UI shows Vector 语义召回 has no results.
errors: No visible backend exception in screenshot. Need inspect local retrieval/index behavior.
reproduction: Run local retrieval/query workflow for “贵州茅台最新的营收数据” and “2026 第一季度贵州茅台营业收入”; inspect retrieval_complete vector_results, rerank top5 metadata, table_facts scoring, and vector index loading. Determine whether rerank cards are table_fact synthetic records, table chunks, or text chunks.
started: After table-aware retrieval and recent K1-K4 fixes were pushed.

## Eliminated
<!-- APPEND only - prevents re-investigating -->

## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-05-14T00:01:00+08:00
  checked: .planning/debug/knowledge-base.md and repository file list
  found: No knowledge-base file exists; relevant modules are under backend/app/core/retrieval, backend/app/core/agent, backend/app/api, and frontend/src components.
  implication: Need direct code investigation; no prior pattern can be tested first.
- timestamp: 2026-05-14T00:02:00+08:00
  checked: retrieval/event/frontend code paths
  found: HybridRetriever.retrieve captures vector_error, but RetrievalCompleteEvent only has bm25_results, vector_results, and fused_top20; frontend RetrievalCompletePayload also lacks error fields and SidebarRight always renders “暂无 Vector 召回结果” for empty vectorDocs.
  implication: A vector failure can be logged server-side but silently displayed as an empty result set in the UI.
- timestamp: 2026-05-14T00:03:00+08:00
  checked: Local HybridRetriever/query_table_facts for “贵州茅台最新的营收数据” and “2026 第一季度贵州茅台营业收入”
  found: Generic latest query returned vector_error dimension mismatch query=1024/index=8 and zero vector results; fused/table_fact top results were FY2024 annual-report facts sorted from 2022/2023/2024 because all scored 7.7. Explicit 2026 Q1 query ranked two 2026Q1 table_fact records first with current_period and strict_period_match.
  implication: Latest-period intent is not represented unless the query contains explicit year/quarter, and vector empty is a real degraded state not a true no-results case.
- timestamp: 2026-05-14T00:06:00+08:00
  checked: Post-fix local retrieval and targeted tests
  found: “贵州茅台最新的营收数据” now ranks 2026Q1 table_fact records first with latest_source/latest_period reasons; vector_error remains explicit for the mock-vs-active embedding dimension mismatch. Backend targeted tests passed and frontend TypeScript lint passed.
  implication: Backend retrieval now prefers latest available period and UI has enough contract data to expose vector degraded state instead of silently empty.

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: Generic “最新/最近/latest” table-fact queries did not encode recency unless an explicit year/quarter was present, so equal-scored annual facts sorted ahead of the latest quarterly facts. Separately, HybridRetriever captured vector_error for index/provider dimension mismatch, but retrieval_complete SSE and frontend snapshot dropped the error, making the UI show an empty Vector panel.
fix: Added latest-source/latest-period filtering and boost for generic latest table metric queries; propagated bm25_error/vector_error through RetrievalCompleteEvent, query streaming, workflow, frontend payload types, and rendered vector degraded state in SidebarRight.
verification: `cd backend && python3 -m pytest tests/test_table_fact_retrieval.py tests/test_query_api.py -q` passed; `cd frontend && npm run lint` passed; local retrieval reproduction ranked 2026Q1 table_fact records first and exposed vector_error.
files_changed: [backend/app/core/retrieval/table_facts.py, backend/app/models/events.py, backend/app/core/agent/workflow.py, backend/app/api/query.py, backend/tests/test_table_fact_retrieval.py, backend/tests/test_query_api.py, frontend/src/api/finrag.ts, frontend/src/types.ts, frontend/src/App.tsx, frontend/src/components/SidebarRight.tsx]
