# Phase 6 Research: PDF Extraction Adapter

**Created:** 2026-05-13  
**Status:** Ready for planning

## Research Goal

Determine the smallest adaptation needed to reuse the provided `pdf2md` project for FinRAG's future ingestion pipeline while preserving no-OCR extraction, idempotency, and traceable raw Markdown outputs.

## Inputs Reviewed

- `.planning/PROJECT.md` — milestone context and current FinRAG direction.
- `.planning/ROADMAP.md` — Phase 6 scope and success criteria.
- `.planning/REQUIREMENTS.md` — `PDF-*` requirements.
- `.planning/phases/06-pdf-extraction-adapter/06-CONTEXT.md` — locked phase decisions.
- `pdf2md/README.md` — current extraction behavior and CLI assumptions.
- `pdf2md/AGENTS.md` — project-specific constraints for `pdf2md`.
- `pdf2md/src/elite_daily_pdf_to_md/cli.py` — command-line entrypoint.
- `pdf2md/src/elite_daily_pdf_to_md/processor.py` — orchestration of extraction + manifests.
- `pdf2md/src/elite_daily_pdf_to_md/extraction.py` — extraction backends.
- `pdf2md/src/elite_daily_pdf_to_md/output.py` — current Markdown output layout.
- `pdf2md/src/elite_daily_pdf_to_md/manifest.py` — failure recording and file traceability.
- `pdf2md/src/elite_daily_pdf_to_md/metadata.py` — filename/title normalization.

## Current Behavior Summary

`pdf2md` already does most of the extraction work needed for Phase 6:

- discovers PDFs in a source directory
- extracts with PyMuPDF or `pymupdf4llm`
- writes Markdown with frontmatter
- records manifests
- skips unchanged files unless forced
- records failures without aborting the batch

The main mismatch is that it is currently tailored to Elite Daily season/vault paths, not FinRAG's generic document-ingestion needs.

## Recommended Technical Approach

### 1. Add a FinRAG-Targeted Output Mode

Introduce a small configuration or CLI mode that allows writing extracted Markdown and manifests into a FinRAG-owned raw data directory, such as `backend/app/data/raw/` or another explicitly documented path.

The goal is not to redesign the extractor, only to make the output destination generic enough for FinRAG.

### 2. Preserve Extraction Metadata

Keep or extend the current frontmatter/manifest fields so each extracted file carries:

- source PDF path/name
- title
- extractor
- status
- page count
- content hash
- error text for failures

This traceability will be useful when Phase 7 maps extracted files into schema JSON.

### 3. Keep Idempotent Batch Semantics

Reuse the current hash-based skip behavior and per-file failure recording. This is essential because document imports should be repeatable and safe to rerun.

### 4. Keep No-OCR Scope

Do not add OCR or scanned-PDF fallback in this phase. The project scope already says the source PDFs are text-layer PDFs.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Elite Daily season assumptions leak into FinRAG | Factor output-path and metadata generation into a reusable adapter layer. |
| Adapting pdf2md becomes a rewrite | Keep the change surface small and reuse current extraction/manifest code. |
| Output format is not suitable for Phase 7 | Ensure extracted Markdown and manifests retain enough metadata for later schema import. |
| OCR creep enters scope | Keep the phase explicitly text-layer only. |

## Recommendation

Plan Phase 6 as two focused execution plans:

1. **FinRAG output adapter** — make `pdf2md` write raw Markdown/metadata to a FinRAG-owned directory and preserve traceability.
2. **Adapter validation and docs** — add tests and documentation proving idempotent extraction and the new output contract.

That is the smallest safe step before building the FinRAG-side import pipeline in Phase 7.
