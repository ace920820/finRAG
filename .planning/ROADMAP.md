# Roadmap: FinRAG v1.2 Frontend Evidence Traceability & Interaction Polish

**Last updated:** 2026-05-13
**Current status:** v1.2 implementation complete; ready for user smoke test.

## Shipped Milestones

| Milestone | Name | Status | Phases | Summary | Archive |
| --- | --- | --- | --- | --- | --- |
| v1.0 | Mock-data MVP | Shipped | 1-5 | FastAPI backend, hybrid retrieval/rerank, SSE query API, React integration, preview rewrite, and mock-data demo readiness. | Prior phase artifacts in `.planning/phases/01-*` through `.planning/phases/05-*` |
| v1.1 | Document Import Pipeline | Shipped | 6-7 | PDF/text-layer extraction, raw Markdown artifacts, FinRAG corpus import, deterministic chunking, and retrieval index rebuild. | `.planning/milestones/v1.1-ROADMAP.md` |

## Current Milestone

### v1.2 Frontend Evidence Traceability & Interaction Polish

Goal: Make the real-corpus demo easier to navigate and fully traceable across multi-turn conversations.

| Phase | Name | Requirements | Goal | Validation |
| --- | --- | --- | --- | --- |
| 8 | Real-Corpus Entry Points | REQ-v1.2-001, REQ-v1.2-002, REQ-v1.2-008 | Update example questions and make document library entries open their source/readable document. | ✓ Complete |
| 9 | Retrieval Sidebar Interaction Polish | REQ-v1.2-003, REQ-v1.2-004, REQ-v1.2-005, REQ-v1.2-008 | Make retrieval panels independently collapsible and improve Rerank detail/score rendering. | ✓ Complete |
| 10 | Per-Turn Evidence Traceability | REQ-v1.2-006, REQ-v1.2-007, REQ-v1.2-008 | Store and restore retrieval/citation snapshots per assistant turn. | ✓ Complete |

## Phase Details

### Phase 8 — Real-Corpus Entry Points

**Purpose:** Align the left sidebar with the imported 40-document corpus and provide a direct path from document names to source content.

**Likely files:**
- `frontend/src/components/SidebarLeft.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/finrag.ts`
- Backend document route only if needed for source opening.

**Success criteria:**
- The three examples use real corpus topics spanning the available companies.
- Document rows behave like links/buttons and open the selected document.
- No secrets or local filesystem-only paths are exposed in committed config.

### Phase 9 — Retrieval Sidebar Interaction Polish

**Purpose:** Make BM25, Vector, and Rerank inspection easier during demo and fix current score/detail display issues.

**Likely files:**
- `frontend/src/components/SidebarRight.tsx`
- `frontend/src/types.ts`
- `frontend/src/api/finrag.ts`

**Success criteria:**
- Panel state is independent, not accordion-exclusive.
- All panels can be collapsed.
- Rerank cards expose full evidence text on click and render scores consistently.

### Phase 10 — Per-Turn Evidence Traceability

**Purpose:** Preserve retrieval provenance per conversation turn so the demo remains auditable after multiple queries.

**Likely files:**
- `frontend/src/App.tsx`
- `frontend/src/types.ts`
- `frontend/src/components/ChatArea.tsx`
- `frontend/src/components/SidebarRight.tsx`

**Success criteria:**
- Each assistant message owns its retrieval snapshot and citation metadata.
- Selecting an older answer/citation makes the right sidebar display that answer's original snapshot.
- Adding a new query no longer overwrites old answers' evidence context.

## Next Action

Run manual frontend smoke test for v1.2 interactions, then complete the milestone.
