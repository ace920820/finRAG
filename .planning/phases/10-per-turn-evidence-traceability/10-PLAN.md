# Phase 10 Plan: Per-Turn Evidence Traceability

## Goal
Make retrieval visualizations and citations traceable per conversation turn.

## Tasks
1. Add evidence snapshot types to frontend message model.
2. Store retrieval/rerank/done citation data on assistant messages during stream handling.
3. Derive sidebar display from selected assistant message snapshot.
4. Select assistant snapshot on answer/citation click.
5. Validate multi-turn behavior with typecheck/build.
