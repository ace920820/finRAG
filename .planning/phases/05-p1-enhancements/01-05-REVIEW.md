# Phase 5 Baseline Review — P1 Enhancements (Preview Rewrite)

Read-only baseline regression review of the optional `/api/preview-rewrite` endpoint.

## Scope

PLAN: `.planning/phases/05-p1-enhancements/05-01-PLAN.md`

Re-validate that:

- `POST /api/preview-rewrite` is deterministic and offline-testable.
- Response shape includes expanded terms, sub-queries, detected entities, intent.
- Endpoint reuses `analyze_query()` and does not drift from main `/api/query` rewrite logic.
- `/api/query` is unaffected.

## Files Audited

- `backend/app/api/preview_rewrite.py`
- `backend/app/main.py`
- `backend/app/core/agent/query_analysis.py`
- `backend/tests/test_preview_rewrite.py`

## Verification Run

- `python3 -m pytest -q tests/test_preview_rewrite.py` (in the full suite, all green).
- Router registration confirmed via `create_app()` path list.

## Findings

### Blocker

None.

### Important

None.

### Nice-to-have

- **[Nice-to-have] `detect_entities` shares heuristics with `_expand_terms` but lives separately**
  - File: `backend/app/core/agent/query_analysis.py:46-58` vs `61-72`.
  - Two parallel hand-maintained lists for the same aliases. Risk of drift when Phase 16 adds new entities (TSMC, semiconductor sector, etc.). Consider consolidating to a single alias map driving both.

- **[Nice-to-have] PreviewRewriteResponse renames `expanded` to `expanded_terms`**
  - File: `backend/app/api/preview_rewrite.py:14`, `backend/app/models/events.py:10`.
  - `QueryRewriteEvent` exposes `expanded`, `PreviewRewriteResponse` exposes `expanded_terms`. Two names for the same data shape. Frontend reads each from its own event, so not broken; cosmetic.

## Phase 15/16 Risk Notes

- If Phase 16 introduces metric/period detection for table routing, `detect_entities` becomes an obvious place to extend. Consider returning structured entities (`type: "company" | "metric" | "period"`) rather than a plain `list[str]` when this happens.

## Recommended Follow-up

1. No code changes recommended for v1.0 baseline.
2. When Phase 16 adds structured entity detection, fold the alias map shared by `_expand_terms` and `detect_entities` into one source of truth.
