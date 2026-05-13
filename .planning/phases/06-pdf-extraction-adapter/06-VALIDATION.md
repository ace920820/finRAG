# Phase 6 Validation Checklist

**Created:** 2026-05-13  
**Updated:** 2026-05-13  
**Status:** Passed

## Goal-Backward Validation

Phase 6 is complete because `pdf2md` now produces FinRAG-usable raw Markdown artifacts with traceable metadata, idempotent behavior, per-file failure recording, and no OCR dependency.

## Evidence

- `pdf2md` has `--profile finrag` for generic financial PDFs.
- FinRAG mode writes Markdown to `<raw-root>/extracted/<collection-name>/`.
- FinRAG mode writes Markdown/JSON manifests to `<raw-root>/_meta/`.
- Markdown/frontmatter and JSON manifests preserve source PDF path/name, title, extraction status, page count, `pdf_sha256`, `content_hash`, and `text_sha256`.
- Unchanged PDFs are skipped unless `--force` is passed.
- Individual extraction failures are recorded in manifest records and do not abort the full batch.
- Existing Elite Daily season behavior remains covered by the old test suite.

## Validation Commands Run

Initial documented command used `python`, but this host does not expose a `python` executable:

```bash
cd pdf2md && python -m pytest tests/test_finrag_adapter.py tests/test_config.py
# zsh:1: command not found: python
```

Successful targeted validation used `python3`:

```bash
cd pdf2md && python3 -m pytest tests/test_finrag_adapter.py tests/test_config.py
# 21 passed in 0.12s
```

Successful full validation:

```bash
cd pdf2md && python3 -m pytest
# 70 passed, 5 warnings in 0.68s
```

The warnings are PyMuPDF/SWIG deprecation warnings from imported dependencies and are not caused by Phase 6 logic.

## Output Contract For Phase 7

Phase 7 can consume:

- Raw Markdown: `<raw-root>/extracted/<collection-name>/*.md`
- Markdown manifest: `<raw-root>/_meta/<collection-name>-extraction-manifest.md`
- JSON manifest: `<raw-root>/_meta/<collection-name>-extraction-manifest.json`

Each successful Markdown file contains clean extracted source text under `## Extracted Text` and metadata in YAML frontmatter. The importer should prefer frontmatter/JSON manifest fields over parsing Markdown headings when building FinRAG documents and chunks.

## Out Of Scope Checks

- OCR was not added.
- FinRAG `documents.json` and `chunks.json` generation was not added.
- Retrieval indexes were not rebuilt.
- Frontend code was not changed.

## Phase 7 Caveats

- Phase 7 still needs the FinRAG-side import/chunk/index pipeline.
- Phase 7 should decide the canonical raw data location, likely `backend/app/data/raw/`.
- Phase 7 should keep demo fixture fallback available while importing real documents.
