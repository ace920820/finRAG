# Phase 1 Baseline Review — Backend Foundation & Demo Data

Read-only baseline regression review of the FastAPI app skeleton, config, and Pydantic schemas after later phases extended them.

## Scope

PLAN: `.planning/phases/01-backend-foundation-and-demo-data/01-01-PLAN.md`

Re-validate that:

- `/health` and `/api/documents` routes are still registered.
- `Document` / `Chunk` / `DocumentListResponse` / SSE event models still match PRD field names.
- `get_settings()` is offline-safe; `demo_mode` defaults True.
- Secrets are never required for import or tests.

## Files Audited

- `backend/app/main.py`
- `backend/app/api/documents.py`
- `backend/app/core/config.py`
- `backend/app/models/schemas.py`
- `backend/app/models/events.py`
- `backend/.env.example`

## Verification Run

- `python3 -c "from app.main import create_app; ..."` → registered paths include `/health`, `/api/documents`, `/api/documents/{doc_id}/view`, `/api/query`, `/api/preview-rewrite`, full `/api/kb/*` set, `/api/debug/retrieval`. All Phase 1 routes still present plus expected later additions.
- `python3 -m pytest -q tests/test_health.py tests/test_documents_api.py tests/test_schemas.py` (part of full suite, all green).
- `git check-ignore -v backend/.env` → `.gitignore:2:.env`. `git ls-files backend/.env` → empty. **Secrets are not committed.** (A real local `.env` exists but is gitignored.)

## Findings

### Blocker

None at the Phase 1 boundary. (The corpus drift surfaced in Phase 2 review is recorded once in the milestone SUMMARY.)

### Important

- **[Important] `/api/documents` returns 4 demo docs while retrieval has 40**
  - File: `backend/app/api/documents.py:14`, `backend/app/core/ingestion/fixture_loader.py:25`.
  - Effect: PRD shape of `DocumentListResponse` is intact, but the data source is stale relative to the cached BM25/vector index. Frontend library shows 4 fixture docs even after the v1.1 corpus import. See milestone SUMMARY Blocker B1 for the cross-cutting root cause.

### Nice-to-have

- **[Nice-to-have] `main.py` uses `dict[str, Union[str, bool]]` PEP 585 syntax**
  - File: `backend/app/main.py:18`. Fine on Python 3.9+ with `from __future__ import annotations` style across the codebase; the file does not have `__future__` import. Currently no runtime impact because route handlers don't introspect annotations, but flagged to keep an eye on if you ever lower the supported Python floor.

- **[Nice-to-have] `Settings.processed_data_dir` is `Optional[Path]` with a `processed_dir` property fallback**
  - File: `backend/app/core/config.py:17,53-55`. Works correctly. Just worth documenting the two-field convention if Phase 15/16 adds more data dirs (e.g., tables/, facts/).

- **[Nice-to-have] `Settings._resolve_path` tries to be clever about `backend/...` prefixed paths**
  - File: `backend/app/core/config.py:61-68`. Behavior matches PLAN, but the heuristic is non-obvious. Acceptable for v1.0; if it ever fights a developer, replace with explicit absolute-path requirement.

- **[Nice-to-have] No router for KB present in original Phase 1 PLAN**
  - Expected since KB routers were added in Phase 11/12. Listed here only to acknowledge the route list has grown; nothing to fix.

## Phase 15/16 Risk Notes

- `Chunk.metadata: dict[str, Any]` is the natural extension point for Phase 15's `chunk_type`, `table_id`, statement type, etc. PLAN already supports this without schema changes.
- `Document` has no `report_period` / `ticker` field. Phase 15 PLAN expects table chunk metadata to include `company/ticker/doc/report-period`. That can land in `Chunk.metadata` without breaking `Document`, but it is worth deciding whether `Document` itself eventually gets explicit `ticker` and `report_period` fields once table-aware retrieval matures.
- `DocumentListItem.chunk_count` is computed from `chunks.json`. After Phase 15, this will include table chunks. Frontend already treats this as an opaque count, so no breaking change expected, but worth a smoke test once table chunks are imported.

## Recommended Follow-up

1. Treat the corpus drift fix as the highest-priority Phase 1 follow-up. Tracked under milestone SUMMARY (B1).
2. No code changes recommended in Phase 1 source itself for v1.0 baseline.
