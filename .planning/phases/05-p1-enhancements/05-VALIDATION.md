# Phase 5 Validation Checklist

**Created:** 2026-05-13

## Goal-Backward Validation

Phase 5 is complete only when the optional rewrite preview is live, debounced, and consistent with the deterministic query analysis used by the main demo path, while the MVP query flow remains unchanged.

## Required Evidence

- `POST /api/preview-rewrite` exists and returns expanded terms and detected entities.
- Preview behavior reuses deterministic query analysis.
- Frontend shows live preview text after typing debounce rather than static mock text.
- Frontend lint and build still pass.
- Backend pytest still passes.

## Validation Commands

```bash
cd backend && python3 -m pytest
cd frontend && npm run lint
cd frontend && npm run build
```

## Manual Smoke Check

1. Open the frontend.
2. Type `宁德时代近期有哪些潜在经营风险？` slowly.
3. Confirm the preview area updates after a short pause.
4. Confirm the preview includes backend-derived expanded terms or entities.
5. Confirm sending the query still runs the Phase 4 SSE flow unchanged.

## Out Of Scope Checks

- No recency-decay rerank implementation required.
- No numeric consistency algorithm required.
- No change to the main query SSE workflow.
