# Phase 6 UAT: PDF Extraction Adapter

**Created:** 2026-05-13  
**Status:** Ready for manual acceptance

## Purpose

Manually verify that the adapted `pdf2md` FinRAG mode can extract real text-layer PDFs into traceable raw Markdown artifacts before Phase 7 imports them into FinRAG schemas and indexes.

## Preconditions

- Source PDFs have a selectable text layer; OCR is not supported in this phase.
- Python dependencies for `pdf2md` are installed.
- Use `python3` on this host if `python` is unavailable.

## Suggested Command

```bash
cd /Volumes/KINGSTON/projects/finRAG/pdf2md
python3 -m elite_daily_pdf_to_md.cli \
  --profile finrag \
  --source-dir "/path/to/source-pdfs" \
  --raw-root "/Volumes/KINGSTON/projects/finRAG/backend/app/data/raw" \
  --collection-name "research-reports" \
  --extractor pymupdf
```

## Manual Checklist

- [ ] Add one or more text-layer PDFs to the source directory.
- [ ] Run the FinRAG extraction command.
- [ ] Confirm Markdown files appear under `backend/app/data/raw/extracted/research-reports/`.
- [ ] Confirm JSON and Markdown manifests appear under `backend/app/data/raw/_meta/`.
- [ ] Open one Markdown file and confirm frontmatter includes `domain: "finrag"`, `collection`, `source_pdf_name`, `source_pdf_path`, `title`, `status`, `page_count`, `pdf_sha256`, `content_hash`, and `text_sha256`.
- [ ] Confirm extracted source text is under `## Extracted Text` and remains clean raw text, not graph-enriched notes.
- [ ] Run the same command again without `--force` and confirm the summary shows unchanged files as skipped.
- [ ] Run with `--force` and confirm files are re-extracted.
- [ ] Optionally add a broken or non-PDF-renamed file with `.pdf` suffix and confirm one failure is recorded while other PDFs still extract.

## Acceptance Criteria

- FinRAG mode accepts generic PDF filenames without Elite Daily season naming.
- Outputs are traceable enough for Phase 7 import.
- Idempotent reruns work.
- Per-file failures are visible in manifests.
- No OCR or index rebuild is implied by this phase.
