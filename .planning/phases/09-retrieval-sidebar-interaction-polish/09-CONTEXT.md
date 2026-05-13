# Phase 9: Retrieval Sidebar Interaction Polish - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Autonomous from v1.2 roadmap and user screenshots

## Phase Boundary

Make BM25, Vector, and Rerank panels independently collapsible and improve Rerank Top 5 detail/score display.

## Implementation Decisions

- Replace single `openPanel` accordion state with independent booleans.
- Allow all panels to be closed.
- Keep citation clicks opening Rerank, but do not force other panels closed.
- Rerank cards should expand/collapse individually and reveal full evidence text.
- Score rendering should use fixed precision and reserve layout space so every item shows the score when available.

## Acceptance Focus

- Chevron toggles collapse/open each panel independently.
- Rerank cards show full text when clicked.
- Scores like 0.18 render consistently for every Top 5 item.
