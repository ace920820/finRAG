# Phase 6–7 Code Review

Review date: 2026-05-14
Scope: Phase 6 PDF extraction adapter and Phase 7 corpus import/index build.

## Summary

- Findings: 4 total
- High: 1
- Medium: 2
- Low: 1
- Review target: current working tree, focusing on Phase 6/7 extraction, raw loading, import, chunking, and index scripts.

## Findings

### High — Empty imports can overwrite the processed corpus with empty files

- File: `backend/app/core/ingestion/corpus_importer.py:53`
- Impact: If `import_corpus()` is called with a wrong `collection_name`, missing `source_dir`, or empty raw folder, it still writes `documents.json` and `chunks.json` at `backend/app/core/ingestion/corpus_importer.py:58`. With the default CLI output path this can erase the active demo corpus by replacing it with `[]`.
- Evidence: `load_raw_documents(...)` can return an empty list, `build_processed_records(...)` then returns empty `documents` and `chunks`, and there is no guard before writing the processed files.
- Recommendation: Fail fast when no raw inputs/documents are discovered unless an explicit `--allow-empty` flag is provided. For extra safety, write to temporary files and atomically replace only after successful non-empty import.

### Medium — Collection names are used as filesystem paths without validation

- File: `pdf2md/src/elite_daily_pdf_to_md/output.py:27`
- Impact: `collection_name` is appended directly into output paths such as `raw_root / "extracted" / collection_name` and manifest paths. A value like `../outside` can write outside the intended `raw_root` tree. The backend import script has the same shape through `backend/app/core/ingestion/raw_loader.py:69` and `backend/scripts/import_corpus.py:24`.
- Evidence: `collection_extracted_dir()` and `collection_manifest_paths()` do not sanitize or validate `collection_name`; CLI parser accepts arbitrary strings.
- Recommendation: Restrict collection names to a safe slug pattern such as `[A-Za-z0-9_-]+`, or sanitize and verify every resolved path remains under `raw_root` before reading/writing.

### Medium — Importer can ingest its own generated outputs when no collection is specified

- File: `backend/app/core/ingestion/raw_loader.py:72`
- Impact: When `collection_name` and `source_dir` are omitted, discovery scans `raw_root / "extracted"`, `raw_root / "manual"`, and then `raw_root` recursively. Because generated Markdown outputs and `_meta` manifests also live under `raw_root`, broad imports can pick up manifest Markdown or duplicate already-discovered extracted/manual files. The `set(paths)` removes exact duplicate paths, but it does not exclude `_meta` or other generated Markdown under the raw root.
- Evidence: `_candidate_roots()` yields `raw_root` at `backend/app/core/ingestion/raw_loader.py:74`, while discovery accepts any `.md`, `.txt`, or `.pdf` under that tree at `backend/app/core/ingestion/raw_loader.py:35`.
- Recommendation: Avoid scanning `raw_root` recursively by default, or explicitly exclude `_meta`, index/processed directories, and generated manifests. Prefer requiring either `collection_name` or `source_dir` for CLI imports.

### Low — Build index script mutates cached settings instead of using environment/config reload

- File: `backend/scripts/build_index.py:43`
- Impact: The script calls `get_settings()`, mutates `settings.processed_data_dir` and `settings.index_dir`, then clears only `_processed_dir`. This works in the current single-process script, but it is brittle because other cached settings-derived paths can remain stale if more settings consumers are added.
- Evidence: `settings.processed_data_dir = args.processed_dir` and `settings.index_dir = args.index_dir` happen after settings construction at `backend/scripts/build_index.py:44`.
- Recommendation: Set `FINRAG_PROCESSED_DATA_DIR` and `FINRAG_INDEX_DIR` before `get_settings()` is called, then clear `get_settings.cache_clear()` and `_processed_dir.cache_clear()` before building.

## Non-Blocking Observations

- `pdf2md/src/elite_daily_pdf_to_md/output.py:50` uses the full source path string to generate collision suffixes. This is deterministic on one machine, but filenames can differ across machines for identical PDFs stored in different absolute locations.
- `backend/app/core/ingestion/raw_loader.py:90` intentionally implements a minimal frontmatter parser. It is enough for Phase 6 generated scalar fields, but it will not support lists or nested YAML if future metadata grows.

## Suggested Verification

- Add a regression test that `import_corpus()` raises and preserves existing `documents.json`/`chunks.json` when no raw inputs are found.
- Add tests that reject unsafe collection names in both `pdf2md` FinRAG mode and backend import CLI paths.
- Add a raw discovery test proving `_meta/*-manifest.md` is not imported as a document.
