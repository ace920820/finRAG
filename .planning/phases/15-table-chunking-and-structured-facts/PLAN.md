# Phase 15 Plan — Table Chunking And Structured Facts

**Status:** Complete  
**Milestone:** v1.3 Table-Aware RAG  
**Depends on:** Phase 14 — Table-Aware PDF Extraction  
**Requirements:** REQ-v1.3-010, REQ-v1.3-011, REQ-v1.3-012  
**Source:** `docs/table处理.txt`

## Goal

Consume Phase 14 table artifacts as first-class backend knowledge units by importing table chunks and extracting a lightweight local financial facts store.

Phase 15 does **not** need to change the public chat API or implement full query routing. It prepares durable table chunks and facts that Phase 16 can use for table-aware retrieval and numeric QA.

## Current Baseline

Phase 14 produces:

- `backend/app/data/raw/tables/<collection>/<source-stem>/<table-id>.json`
- `backend/app/data/raw/tables/<collection>/<source-stem>/<table-id>.csv`
- `backend/app/data/raw/_meta/<collection>-table-manifest.json`
- `backend/app/data/raw/_meta/<collection>-table-manifest.md`

Validation from Phase 14:

- Source PDFs: 40
- Extracted tables: 4128
- Table extraction failed sources: 0
- Text import baseline: 40 documents / 9303 text chunks

There are already uncommitted implementation traces in the working tree for table chunks in `backend/app/core/ingestion/corpus_importer.py`; Phase 15 execution should review, complete, and test that work rather than duplicate it.

## Scope

### In Scope

- Extend the backend import pipeline to append `chunk_type=table` chunks from Phase 14 table JSON artifacts.
- Preserve all existing text chunks, document IDs, and public API response compatibility.
- Add row-level `chunk_type=table_row` chunks for high-value financial statement rows where stable enough.
- Generate a local structured facts file for core financial metrics.
- Normalize core metrics:
  - revenue
  - gross profit
  - operating income
  - net income
  - EPS / diluted EPS where available
- Preserve source traceability for every table chunk/fact:
  - `doc_id`
  - `chunk_id` where applicable
  - `table_id`
  - source PDF name/path
  - page number
  - company
  - doc type
  - collection
  - row/column labels
  - raw cell value
- Add deterministic IDs for table chunks, table-row chunks, and facts.
- Add tests for import compatibility, table chunk creation, fact extraction, and index build compatibility.

### Out Of Scope

- No LLM-based table summarization.
- No OCR or chart extraction.
- No SQL database requirement; JSON facts are enough for this demo phase.
- No frontend UI changes.
- No full query router or answer-generation changes; that belongs to Phase 16.
- No broad refactor of retrieval scoring except minimal compatibility safeguards if needed.

## Target Data Contracts

### Chunk Metadata

Text chunks keep existing schema and metadata.

Table chunks should use existing `Chunk` schema and add metadata:

```json
{
  "chunk_type": "table",
  "table_id": "tbl-...",
  "table_title": "Condensed Consolidated Statements of Income",
  "table_json_path": "backend/app/data/raw/tables/.../tbl-....json",
  "table_csv_path": "backend/app/data/raw/tables/.../tbl-....csv",
  "row_count": 12,
  "column_count": 4,
  "extraction_method": "pdfplumber"
}
```

Table-row chunks should add:

```json
{
  "chunk_type": "table_row",
  "table_id": "tbl-...",
  "row_index": 3,
  "metric": "revenue",
  "statement_type": "income_statement",
  "unit": "USD millions",
  "currency": "USD"
}
```

### Facts Store

Write JSON under:

- `backend/app/data/processed/table_facts.json`

Recommended fact shape:

```json
{
  "fact_id": "fact-...",
  "doc_id": "doc-...",
  "table_id": "tbl-...",
  "company": "NVIDIA",
  "doc_type": "financial_report",
  "source_pdf_name": "NVDA_nvidia_10q_FY2026Q3_2025-11-19_q4cdn.pdf",
  "page_num": 7,
  "statement_type": "income_statement",
  "metric": "revenue",
  "metric_label": "Revenue",
  "period_label": "Three Months Ended Oct 26 2025",
  "value": 57006,
  "raw_value": "57,006",
  "unit": "USD millions",
  "currency": "USD",
  "collection": "finrag-user-source-40"
}
```

## Implementation Tasks

### 1. Finalize table artifact loading

- Add a small backend ingestion module if needed, e.g. `backend/app/core/ingestion/table_artifacts.py`.
- Load per-table JSON files from `raw/tables/<collection>/<source-stem>/`.
- Ignore macOS AppleDouble files named `._*`.
- Treat malformed table JSON as skipped with no import failure.
- Preserve deterministic ordering by table path/name.

**Verify**

- Unit test loads valid table JSON and skips invalid `._*` artifacts.
- Existing Markdown/TXT import tests still pass.

### 2. Import `table` chunks

- Extend `build_processed_records()` to append table chunks after text chunks for the same document.
- Keep text chunk ordering unchanged.
- Set deterministic chunk IDs from `doc_id`, `table_id`, and rendered table content.
- Render table chunk content as compact structured text plus Markdown table:
  - title
  - page
  - company/doc metadata
  - Markdown table
- Add `chunk_type=table` and source metadata.

**Verify**

- Importing a raw markdown file with linked table artifacts produces text chunks plus table chunks.
- Re-running import produces identical table chunk IDs.
- Importing documents without table artifacts behaves exactly as before.

### 3. Add `table_row` chunks for core metrics

- Parse each table rows/headers from table JSON.
- Identify financial-statement-like tables with heuristics:
  - table title contains income / statement / operations / comprehensive income, or
  - rows contain revenue / gross profit / operating income / net income / EPS.
- Create one row chunk for rows matching core metrics.
- Render row chunks as concise metric facts with all column values.
- Add metadata for normalized metric, row index, table id, page, statement type, unit/currency when inferred.

**Verify**

- A synthetic income statement table creates one `table_row` chunk for `Revenue`.
- Non-financial/noisy tables do not create row chunks unless they match target metrics.

### 4. Generate structured facts JSON

- Add fact extraction in the importer, returning/writing facts alongside documents/chunks.
- Extend `ImportResult` with optional `facts_path` and `facts` fields, or write through a dedicated helper while preserving existing callers.
- Write `table_facts.json` to the processed dir.
- Normalize numeric values:
  - handle commas, parentheses for negatives, dashes/blank values.
  - keep `raw_value` even when numeric parsing fails.
- Infer currency/unit from table title, source, or labels using simple heuristics:
  - NVIDIA → USD millions when values come from SEC-style statements.
  - TSMC → NT$ / NT dollars if labels indicate.
  - Chinese A-share reports → RMB / CNY if labels indicate.
- Keep inference conservative; unknown is acceptable.

**Verify**

- Synthetic income statement produces facts with `metric=revenue`, `value=57006`, source page/table/doc metadata.
- Facts are deterministic across re-runs.
- Empty or malformed values do not crash import.

### 5. Keep index build compatible

- Ensure BM25 and vector index builders accept `table` and `table_row` chunks without schema changes.
- Avoid requiring facts for existing query endpoints.
- Rebuild indexes with mock providers after importing the 40-PDF corpus.

**Verify**

- `backend/scripts/import_corpus.py --rebuild-index` succeeds.
- `GET /api/documents` and `POST /api/query` remain compatible.
- Existing NVIDIA FY2026 Q3 revenue smoke test still passes or improves.

## Likely Files

Backend code:

- `backend/app/core/ingestion/corpus_importer.py`
- `backend/app/core/ingestion/table_artifacts.py` (optional)
- `backend/app/core/ingestion/table_facts.py` (recommended)
- `backend/app/core/ingestion/normalizer.py` if schema normalization needs metadata defaults
- `backend/app/models/schemas.py` only if `ImportResult` changes require typed helpers; avoid public API schema churn
- `backend/scripts/import_corpus.py`

Backend tests:

- `backend/tests/test_corpus_import.py`
- `backend/tests/test_import_pipeline_integration.py`
- `backend/tests/test_hybrid_retrieval.py`
- `backend/tests/test_table_facts.py` (recommended)

Generated validation artifacts:

- `backend/app/data/processed/table_facts.json`
- `backend/app/data/processed/chunks.json`
- `backend/app/data/index/*`

Generated raw table artifacts from Phase 14 are ignored and should not be committed unless explicitly requested.

## Verification Commands

Run targeted ingestion tests:

```bash
python3 -m pytest \
  backend/tests/test_corpus_import.py \
  backend/tests/test_import_pipeline_integration.py \
  backend/tests/test_table_facts.py
```

Re-import the 40-PDF corpus with table artifacts available:

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

Confirm output counts:

```bash
python3 - <<'PY'
import json
from pathlib import Path
chunks = json.loads(Path('backend/app/data/processed/chunks.json').read_text(encoding='utf-8'))
facts = json.loads(Path('backend/app/data/processed/table_facts.json').read_text(encoding='utf-8'))
print('total_chunks', len(chunks))
print('table_chunks', sum(1 for c in chunks if c.get('metadata', {}).get('chunk_type') == 'table'))
print('table_row_chunks', sum(1 for c in chunks if c.get('metadata', {}).get('chunk_type') == 'table_row'))
print('facts', len(facts))
PY
```

Run retrieval/query regressions:

```bash
python3 -m pytest \
  backend/tests/test_query_api.py \
  backend/tests/test_hybrid_retrieval.py \
  backend/tests/test_documents_api.py \
  backend/tests/test_kb_api.py
```

## Acceptance Criteria

- Existing text-only imports remain backward compatible.
- Table artifacts from Phase 14 produce first-class `table` chunks.
- Core financial rows produce `table_row` chunks where the metric can be recognized.
- `table_facts.json` exists after import and contains deterministic core financial facts.
- Every table chunk/fact has traceable source metadata: document, table, source PDF, page, company, collection.
- The 40-PDF corpus imports and indexes successfully.
- Existing public APIs still pass regression tests.
- No frontend changes are required.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Phase 14 extracted many noisy tables | Only create row chunks/facts for recognized core financial metrics; keep raw table chunks for traceability. |
| Units/currency are ambiguous | Keep `raw_value` and use conservative inference; unknown unit/currency is acceptable. |
| Chunk count grows too much | Add only one table chunk per table and row chunks only for core metrics. |
| Facts duplicate across re-runs | Use deterministic `fact_id` based on doc/table/metric/period/value. |
| Existing query behavior changes unexpectedly | Preserve text chunks, keep public schemas stable, and run existing query/retrieval tests. |

## Handoff To Phase 16

Phase 16 should use `table` / `table_row` chunks and `table_facts.json` to implement table-aware retrieval and numeric QA. Phase 15 only guarantees that table evidence and facts are imported, deterministic, and queryable by future backend logic.


## Execution Summary

- Imported Phase 14 table artifacts as `chunk_type=table` chunks.
- Added core-metric `chunk_type=table_row` chunks for recognized financial rows.
- Generated `backend/app/data/processed/table_facts.json` with deterministic fact IDs and traceability metadata.
- Rebuilt the 40-PDF corpus with mock providers: 40 documents, 9303 text chunks, 4128 table chunks, 660 table_row chunks, and 1558 facts.
- Passed targeted ingestion, table facts, retrieval, documents, query, and KB API regressions.
