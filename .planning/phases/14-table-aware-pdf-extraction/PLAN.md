# Phase 14 Plan — Table-Aware PDF Extraction

**Status:** Complete  
**Milestone:** v1.3 Knowledge Base Management  
**Requirements:** REQ-v1.3-009, REQ-v1.3-010  
**Source:** `docs/table处理.txt`

## Goal

Extend the existing `pdf2md --profile finrag` raw extraction pipeline so PDF tables are preserved as structured artifacts alongside the current raw Markdown text output.

Phase 14 does **not** change backend retrieval behavior yet. It prepares reliable table artifacts for Phase 15 and Phase 16.

## Scope

### In Scope

- Add table-aware extraction to the `pdf2md` FinRAG profile.
- Prefer `pdfplumber` first for table objects because it is lightweight and suitable for text-layer financial PDFs.
- Preserve existing PyMuPDF text extraction and Markdown raw output behavior.
- Emit table artifacts under the backend raw data directory.
- Emit a table manifest summarizing extraction success/failure per source PDF.
- Ensure table extraction failures degrade to text-only extraction.
- Add tests using small synthetic or fixture PDFs where possible.

### Out Of Scope

- No OCR.
- No chart extraction.
- No backend `chunk_type` import changes; that belongs to Phase 15.
- No structured financial facts store; that belongs to Phase 15.
- No query routing or table-aware QA changes; that belongs to Phase 16.
- No frontend UI changes unless required to keep build/tests green.

## Target Output Shape

For each FinRAG collection, extraction should continue writing:

- `backend/app/data/raw/extracted/<collection>/*.md`
- `backend/app/data/raw/_meta/<collection>-extraction-manifest.json`
- `backend/app/data/raw/_meta/<collection>-extraction-manifest.md`

Phase 14 adds table-specific artifacts:

- `backend/app/data/raw/tables/<collection>/<source-stem>/<table-id>.json`
- `backend/app/data/raw/tables/<collection>/<source-stem>/<table-id>.csv`
- `backend/app/data/raw/_meta/<collection>-table-manifest.json`
- `backend/app/data/raw/_meta/<collection>-table-manifest.md`

Recommended table JSON fields:

```json
{
  "table_id": "stable-table-id",
  "collection": "finrag-user-source-40",
  "source_pdf_name": "NVDA_nvidia_10q_FY2026Q3_2025-11-19_q4cdn.pdf",
  "source_pdf_path": "...",
  "page_num": 3,
  "table_index": 1,
  "title": "Condensed Consolidated Statements of Income",
  "headers": ["Metric", "Three Months Ended Oct 26 2025", "Three Months Ended Oct 27 2024"],
  "rows": [["Revenue", "57,006", "35,082"]],
  "markdown": "| Metric | ... |",
  "row_count": 1,
  "column_count": 3,
  "extraction_method": "pdfplumber",
  "status": "extracted",
  "error": ""
}
```

## Implementation Tasks

1. Add table extraction primitives in `pdf2md`.
   - Add a `TableExtractionResult` / table record model under `pdf2md/src/elite_daily_pdf_to_md/`.
   - Implement `pdfplumber`-based table extraction that returns page-level table objects.
   - Normalize empty cells, repeated whitespace, and fully blank rows/columns.
   - Convert extracted rows into Markdown and CSV-safe data.

2. Add table artifact writers.
   - Add helper functions for table artifact paths under `raw/tables/<collection>/<source-stem>/`.
   - Write per-table JSON.
   - Write per-table CSV.
   - Write collection-level JSON and Markdown table manifests.
   - Use stable IDs based on source PDF hash, page number, and table index.

3. Integrate with FinRAG profile.
   - Update `process_finrag_collection` / `_process_pdf` so table extraction runs after successful text extraction.
   - Continue writing the same raw Markdown document as today.
   - Include table artifact references in the Markdown frontmatter or metadata section where useful.
   - If table extraction raises, record table extraction failure but keep the PDF text extraction successful.

4. Add dependency/config support.
   - Add `pdfplumber` to the relevant `pdf2md` dependency file.
   - Keep extraction optional at runtime with a clear error message if `pdfplumber` is unavailable.
   - Do not add heavyweight tools such as Camelot/Tabula/Docling in this phase.

5. Add tests.
   - Verify FinRAG extraction still emits raw Markdown.
   - Verify a PDF with a simple table emits JSON/CSV artifacts and table manifest records.
   - Verify stable re-run/idempotency behavior.
   - Verify table extraction failure does not fail text extraction.

6. Reprocess the 40-PDF demo corpus as a validation step.
   - Run `pdf2md --profile finrag` against `data/docs/source_documents` into `backend/app/data/raw`.
   - Confirm the 40 current documents can still be imported and indexed after table artifacts are added.
   - Confirm table artifacts exist for at least NVIDIA income statement pages if extraction supports them.

## Likely Files

- `pdf2md/pyproject.toml`
- `pdf2md/src/elite_daily_pdf_to_md/extraction.py`
- `pdf2md/src/elite_daily_pdf_to_md/finrag.py`
- `pdf2md/src/elite_daily_pdf_to_md/output.py`
- `pdf2md/src/elite_daily_pdf_to_md/manifest.py`
- `pdf2md/tests/test_finrag_adapter.py`
- `pdf2md/tests/test_extraction.py`
- `backend/app/data/raw/_meta/*` generated during validation
- `backend/app/data/raw/tables/*` generated during validation

## Verification Commands

Run targeted pdf2md tests:

```bash
cd pdf2md
PYTHONPATH=src python3 -m pytest tests/test_finrag_adapter.py tests/test_extraction.py
```

Run FinRAG extraction on the demo source corpus:

```bash
cd pdf2md
PYTHONPATH=src python3 -m elite_daily_pdf_to_md.cli \
  --profile finrag \
  --source-dir ../data/docs/source_documents \
  --raw-root ../backend/app/data/raw \
  --collection-name finrag-user-source-40 \
  --extractor pymupdf \
  --force
```

Re-import and rebuild indexes after extraction:

```bash
FINRAG_EMBEDDING_PROVIDER=mock \
FINRAG_RERANK_PROVIDER=mock \
FINRAG_TEXT_PROVIDER=mock \
python3 backend/scripts/import_corpus.py \
  --collection-name finrag-user-source-40 \
  --processed-dir "$PWD/backend/app/data/processed" \
  --index-dir "$PWD/backend/app/data/index" \
  --rebuild-index
```

Run backend regression checks:

```bash
python3 -m pytest \
  backend/tests/test_kb_api.py \
  backend/tests/test_import_pipeline_integration.py \
  backend/tests/test_query_api.py
```

## Acceptance Criteria

- Existing FinRAG raw Markdown extraction remains backward compatible.
- Table extraction produces table JSON/CSV artifacts for extractable tables.
- Table manifest records source PDF, page, table id, row/column count, status, and artifact paths.
- A table extraction failure does not fail or erase text extraction output.
- Reprocessing the 40-PDF demo corpus still results in 40 documents and 9303 text chunks after backend import.
- No query/retrieval behavior is required to change in Phase 14.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| `pdfplumber` misses borderless financial tables | Still keep text extraction; Phase 14 records partial/no-table status instead of failing. |
| Table rows are noisy or multi-line | Normalize blank rows/cells and preserve raw rows for later Phase 15 refinement. |
| Generated table artifacts become too large | Store per-source subdirectories and manifests; keep generated raw artifacts out of git if existing ignore rules apply. |
| Pipeline accidentally changes document counts | Include explicit validation that the 40-PDF corpus still imports to 40 documents. |

## Handoff To Phase 15

Phase 15 should consume the table artifacts from `backend/app/data/raw/tables/` and `*-table-manifest.json` to create table-aware chunk types and structured financial facts. Phase 14 only guarantees that these artifacts exist and preserve source structure.


## Completion Summary

Completed on 2026-05-14.

- Added `pdf2md` table extraction support with `pdfplumber` for the FinRAG profile.
- Preserved existing PyMuPDF text extraction and raw Markdown output behavior.
- Added table JSON/CSV artifact writing under `backend/app/data/raw/tables/<collection>/<source-stem>/`.
- Added collection-level table manifests under `backend/app/data/raw/_meta/<collection>-table-manifest.{md,json}`.
- Table extraction failures are isolated from text extraction and recorded in the table manifest.
- Reprocessed the 40-PDF demo corpus successfully: 40 extracted, 0 failed.
- Validation table manifest reported 40 sources, 4128 extracted tables, and 0 table extraction failures.
- Backend re-import validation preserved 40 documents and 9303 chunks.

## Validation Results

```bash
cd pdf2md && uv run pytest
# 72 passed

cd pdf2md && uv run python -m elite_daily_pdf_to_md.cli   --profile finrag   --source-dir ../data/docs/source_documents   --raw-root ../backend/app/data/raw   --collection-name finrag-user-source-40   --extractor pymupdf   --force
# Total PDFs: 40; Extracted: 40; Failed: 0

FINRAG_EMBEDDING_PROVIDER=mock FINRAG_RERANK_PROVIDER=mock FINRAG_TEXT_PROVIDER=mock python3 backend/scripts/import_corpus.py   --collection-name finrag-user-source-40   --processed-dir "$PWD/backend/app/data/processed"   --index-dir "$PWD/backend/app/data/index"   --rebuild-index
# Documents: 40; Chunks: 9303

cd backend && python3 -m pytest   tests/test_import_pipeline_integration.py   tests/test_query_api.py   tests/test_hybrid_retrieval.py
# 7 passed
```
