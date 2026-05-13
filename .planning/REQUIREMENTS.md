# Requirements: FinRAG v1.2 Frontend Evidence Traceability & Interaction Polish

**Milestone:** v1.2 Frontend Evidence Traceability & Interaction Polish
**Last updated:** 2026-05-13

## Goal

Improve the real-corpus FinRAG demo UI so users can quickly start relevant questions, open source documents, inspect retrieval evidence, and revisit previous turns without losing the retrieval context that produced each answer.

## Active Requirements

| ID | Requirement | Priority | Acceptance Criteria |
| --- | --- | --- | --- |
| REQ-v1.2-001 | Real-corpus example questions | Must | Left sidebar shows exactly three examples labeled factual / analytical / reasoning; questions are rewritten around the imported corpus companies 宁德时代、贵州茅台、NVIDIA、台积电; clicking each example still starts the query flow. |
| REQ-v1.2-002 | Document list open action | Must | Clicking a document in the left document library opens the corresponding document source or readable document view; the action works for imported corpus entries and does not break query submission. |
| REQ-v1.2-003 | Independent retrieval panel collapse | Must | BM25, Vector, and Rerank panels each toggle via the title chevron; any combination can be open or closed; all three can be closed at the same time. |
| REQ-v1.2-004 | Rerank evidence detail display | Must | Clicking a Rerank Top 5 item reveals the specific text snippet/content used as evidence; long text remains readable without destroying the sidebar layout. |
| REQ-v1.2-005 | Rerank score rendering | Must | Every Rerank Top 5 item consistently displays its score when provided, including values around `0.18`; missing scores degrade gracefully. |
| REQ-v1.2-006 | Per-turn retrieval snapshots | Must | Each assistant answer stores its own BM25, Vector, Rerank, and citation metadata; selecting/clicking an older answer restores that turn's retrieval visualization instead of showing the latest turn. |
| REQ-v1.2-007 | Citation-to-evidence traceability | Must | Citation clicks from an older answer resolve against that answer's original Rerank/citation snapshot, not the latest query's results. |
| REQ-v1.2-008 | Regression-safe demo flow | Should | Existing `/api/documents`, `/api/query`, preview rewrite, answer streaming, and reset behavior continue to work; frontend type/lint/build checks pass. |

## Non-Goals

- No full UI redesign or new visual design system.
- No new retrieval algorithm work unless needed to preserve existing data shape for per-turn snapshots.
- No OCR or corpus import changes.
- No provider/model configuration changes.

## Design Notes

- Prefer storing retrieval snapshots on the assistant message object rather than global singleton state.
- Sidebar can display the active message snapshot; active message should update when the user clicks an answer/citation.
- Document opening can use a minimal backend static/file endpoint if browser cannot directly access source files.
- Keep implementation small and compatible with the current React state architecture.
