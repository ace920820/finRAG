# Phase 6: PDF Extraction Adapter - Context

**Gathered:** 2026-05-13  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 adapts the provided `pdf2md/` project so it can serve FinRAG's document-ingestion pipeline. The goal is to make PDF text-layer extraction reusable for general financial documents and emit traceable raw Markdown / metadata outputs that Phase 7 can later import into FinRAG schema JSON and indexes.

This phase does **not** build the FinRAG import CLI yet. It focuses on adapting extraction, output paths, and metadata so the `pdf2md` tool can produce stable raw artifacts for downstream import.

</domain>

<decisions>
## Implementation Decisions

### Reuse Strategy
- **D-01:** Reuse the existing `pdf2md` extraction, discovery, metadata, output, and manifest concepts instead of rewriting them from scratch.
- **D-02:** Preserve the no-OCR constraint.
- **D-03:** Keep idempotent skip-on-unchanged behavior and per-file failure recording.
- **D-04:** Support both single-PDF and batch directory processing for generic financial documents.

### FinRAG Adaptation
- **D-05:** Add a FinRAG-oriented raw output path for extracted Markdown/metadata instead of only the Elite Daily vault layout.
- **D-06:** Keep source traceability fields: source PDF path/name, title, page count, hash, extractor, status, and error message.
- **D-07:** Maintain Markdown frontmatter or equivalent metadata so Phase 7 can import the outputs reliably.
- **D-08:** The adapter should be able to output to a FinRAG data directory without depending on the original Obsidian vault structure.

### Scope Control
- **D-09:** Do not add OCR, image understanding, or table-vision systems in this phase.
- **D-10:** Do not build the FinRAG schema import pipeline yet.
- **D-11:** Do not introduce new external extraction frameworks unless required to adapt the existing code.
- **D-12:** Keep the code changes localized to `pdf2md/` and a small set of docs/config files.

### the agent's Discretion
- The agent may choose whether the FinRAG raw output is a new directory under `backend/app/data/raw/` or another documented path, as long as it is explicit and consistent.
- The agent may choose the exact adapter CLI/API shape for the adapted extractor.
- The agent may add a minimal config file or alias layer to support FinRAG-specific output paths.

</decisions>

<specifics>
## Specific Ideas

- `pdf2md/src/elite_daily_pdf_to_md/extraction.py` already has both PyMuPDF and `pymupdf4llm` paths, which is ideal for a FinRAG adapter.
- `pdf2md/src/elite_daily_pdf_to_md/manifest.py` already captures useful traceability fields and can be extended or reused for FinRAG outputs.
- `pdf2md/src/elite_daily_pdf_to_md/output.py` is the most likely place to redirect output paths and frontmatter for a FinRAG raw layer.
- The current `pdf2md` CLI assumes season-based Elite Daily input; Phase 6 should broaden or parameterize this assumption.

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project And Scope
- `.planning/PROJECT.md` — overall milestone goals and scope boundary.
- `.planning/ROADMAP.md` — Phase 6 goal and success criteria.
- `.planning/REQUIREMENTS.md` — `PDF-*` requirements.
- `.planning/STATE.md` — current phase and milestone state.
- `pdf2md/AGENTS.md` — required coding behavior for files under `pdf2md/`.

### Source Code
- `pdf2md/README.md` — current extraction behavior and CLI usage.
- `pdf2md/src/elite_daily_pdf_to_md/cli.py` — entrypoint and current assumptions.
- `pdf2md/src/elite_daily_pdf_to_md/processor.py` — batch processing and manifest wiring.
- `pdf2md/src/elite_daily_pdf_to_md/extraction.py` — PDF extraction implementations.
- `pdf2md/src/elite_daily_pdf_to_md/metadata.py` — filename/title normalization.
- `pdf2md/src/elite_daily_pdf_to_md/output.py` — Markdown output format and file paths.
- `pdf2md/src/elite_daily_pdf_to_md/manifest.py` — per-file and per-run manifest generation.

### FinRAG Integration References
- `.planning/frontend-integration-readiness.md` — existing frontend/backend contract baseline.
- `backend/app/data/processed/*.json` — current fixture-based document/chunk shapes that Phase 7 will eventually replace or augment.
- `backend/app/core/ingestion/fixture_loader.py` — current fixture loading entrypoint.

</canonical_refs>

<code_context>
## Existing Code Insights

### `pdf2md`
- Already extracts text-layer PDFs without OCR.
- Already records manifest status and errors per file.
- Already supports idempotent skip behavior using PDF hashes and frontmatter.
- Current output assumes an Obsidian vault hierarchy and Elite Daily naming conventions.

### FinRAG
- Phase 5 completed the main demo path; the next gap is real ingestion.
- The backend currently depends on `backend/app/data/processed/*.json` fixture data.
- Phase 7 will need a stable raw output contract from Phase 6.

</code_context>

<deferred>
## Deferred Ideas

- OCR for scanned PDFs.
- Entity graph extraction from PDFs.
- FinRAG schema import and index rebuild.
- Full table reconstruction and normalization beyond extracted text.

</deferred>

---

*Phase: 06-pdf-extraction-adapter*
*Context gathered: 2026-05-13*
