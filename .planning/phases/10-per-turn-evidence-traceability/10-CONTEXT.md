# Phase 10: Per-Turn Evidence Traceability - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Autonomous from v1.2 roadmap and user screenshots

## Phase Boundary

Preserve retrieval and citation evidence for each assistant answer so older turns remain traceable after later queries.

## Implementation Decisions

- Store BM25, Vector, Rerank, and citations on each assistant message as an evidence snapshot.
- Maintain an active assistant message ID for right-sidebar display.
- Clicking an assistant message or citation selects that message's snapshot.
- Citation IDs are scoped to the selected assistant message, preventing old citations from resolving against the latest turn.

## Acceptance Focus

- New queries no longer overwrite old turns' retrieval evidence.
- Selecting an older answer restores its BM25/Vector/Rerank sidebar data.
- Citation clicks from old answers activate the correct old Rerank evidence item.
