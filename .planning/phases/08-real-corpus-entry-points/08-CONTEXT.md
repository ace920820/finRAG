# Phase 8: Real-Corpus Entry Points - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Autonomous from v1.2 roadmap and user request

## Phase Boundary

Update left-sidebar example questions around the imported real corpus and make document library entries open their corresponding documents.

## Implementation Decisions

- Use three fixed example questions labeled factual / analytical / reasoning.
- Cover the imported corpus companies across the example set: 宁德时代、贵州茅台、NVIDIA、台积电.
- Prefer minimal backend endpoint for document viewing because browser cannot open local source file paths directly.
- Open documents in a new tab using a local API route that renders readable text/Markdown.

## Acceptance Focus

- Example clicks still submit queries.
- Document clicks open the selected document.
- Existing `/api/documents` remains compatible with frontend list loading.
