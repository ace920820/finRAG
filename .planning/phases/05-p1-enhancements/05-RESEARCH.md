# Phase 5 Research: P1 Enhancements

**Created:** 2026-05-13  
**Status:** Ready for planning

## Research Goal

Identify the smallest safe implementation for the optional rewrite preview enhancement so the frontend can show live, debounced query expansion feedback without altering the stable Phase 4 query flow.

## Inputs Reviewed

- `.planning/ROADMAP.md` — Phase 5 goal and optional enhancement scope.
- `.planning/REQUIREMENTS.md` — `API-10` and v2 quality enhancement references.
- `.planning/phases/05-p1-enhancements/05-CONTEXT.md` — locked low-risk enhancement decisions.
- `.planning/phases/04-integration-and-demo-hardening/04-VERIFICATION.md` — completed integration baseline.
- `backend/app/core/agent/query_analysis.py` — deterministic query rewrite logic.
- `backend/app/api/query.py` — main SSE workflow that must remain stable.
- `frontend/src/components/ChatArea.tsx` — existing typing preview area.
- `frontend/src/api/finrag.ts` — central frontend adapter module.
- `frontend/src/App.tsx` — current frontend/backend shell.

## Recommended Technical Approach

### 1. Backend Preview Endpoint

Add `POST /api/preview-rewrite` that accepts the existing `QueryRequest` schema or a lightweight preview payload and returns:

- `original`
- `expanded_terms`
- `sub_queries`
- `detected_entities`
- `intent` if useful for preview labeling

Reuse `analyze_query()` directly so preview behavior matches the main query workflow. This keeps the enhancement deterministic, cheap, and aligned with the actual SSE query path.

### 2. Lightweight Entity Extraction

For preview clarity, extract detected company entities from the query using the same alias map already embedded in query analysis.

This can be as simple as a helper that returns companies/aliases such as:

- `贵州茅台`
- `宁德时代`
- `CATL`

No broader entity system is needed for Phase 5.

### 3. Frontend Debounced Preview

Use the existing typing preview section in `ChatArea` or a small hook in `App.tsx` to call the preview endpoint after a debounce.

Recommended behavior:

- Wait ~500ms after the user stops typing.
- Cancel in-flight preview requests when input changes.
- Show preview keywords from backend when available.
- Keep the current placeholder text for empty input.

### 4. Validation

Keep validation modest and deterministic:

- Backend pytest for preview endpoint shape and entity extraction.
- Frontend `npm run lint` and `npm run build`.

Do not introduce an expensive browser test framework or alter the main SSE flow.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Preview endpoint diverges from main query rewrite behavior | Reuse `analyze_query()` and shared alias/entity logic. |
| Debounced preview causes stale responses to flash | Cancel prior request with `AbortController` and ignore stale results. |
| Preview UI becomes a new feature surface | Keep the current single-line preview area and existing layout. |
| Enhancement spills into broader quality work | Explicitly defer numeric consistency and recency decay. |

## Recommendation

Plan Phase 5 as two focused execution plans:

1. **Preview rewrite backend** — add `POST /api/preview-rewrite` plus tests.
2. **Frontend debounced preview wiring** — replace the static preview text with live backend preview data, then validate backend/frontend builds.

This delivers the only required Phase 5 feature while keeping the demo path stable.
