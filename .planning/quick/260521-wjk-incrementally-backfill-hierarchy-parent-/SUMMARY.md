# Quick Task 260521-wjk Summary

## Outcome

Implemented incremental hierarchy backfill without recomputing existing vectors.

## Changes

- Added `backend/scripts/backfill_hierarchy.py`.
- Added `backend/tests/test_hierarchy_backfill.py`.
- Backfilled existing corpus/index:
  - processed chunks: 14694
  - vector chunks/vectors: 14694 / 14694
  - vector provenance: silicon / BAAI/bge-m3 / 1024
  - parents with children: 895
  - children with parent links: 9963

## Verification

- `cd backend && python3 -m pytest tests/test_hierarchy_backfill.py` -> 2 passed
- `cd backend && python3 -m pytest tests/test_hierarchy_backfill.py tests/test_hybrid_retrieval.py tests/test_query_api.py tests/test_retrieval_index.py` -> 22 passed
- Live debug retrieval for `宁德时代近期有哪些潜在经营风险？` returned `hierarchy_drill_down` with 14 parent candidates and 8 expanded children.

## Notes

Backfill used deterministic page-window section parents for legacy text chunks because the existing processed corpus did not preserve original heading paths. It did not re-embed the original 14091 chunks; it embedded only newly appended section parent chunks on the first run, then synchronized them into processed chunks on the idempotent second run.
