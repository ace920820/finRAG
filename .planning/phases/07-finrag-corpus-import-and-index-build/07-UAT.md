# Phase 7 UAT: FinRAG Corpus Import And Index Build

**Created:** 2026-05-13  
**Status:** Ready for manual real-corpus smoke test

## Purpose

Verify the real document ingestion path with user-provided PDFs or Markdown after automated tests have passed.

## Checklist

- [ ] Put source PDFs in a local folder outside git, such as `/Volumes/KINGSTON/finrag-source-pdfs`.
- [ ] Extract PDFs with Phase 6 command:

```bash
cd /Volumes/KINGSTON/projects/finRAG/pdf2md
python3 -m elite_daily_pdf_to_md.cli \
  --profile finrag \
  --source-dir "/Volumes/KINGSTON/finrag-source-pdfs" \
  --raw-root "/Volumes/KINGSTON/projects/finRAG/backend/app/data/raw" \
  --collection-name "research-reports" \
  --extractor pymupdf
```

- [ ] Optionally add manual `.md` or `.txt` files under `backend/app/data/raw/manual/research-reports/`.
- [ ] Import corpus and rebuild indexes:

```bash
cd /Volumes/KINGSTON/projects/finRAG/backend
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name research-reports \
  --processed-dir app/data/processed \
  --index-dir app/data/index \
  --rebuild-index
```

- [ ] Start backend:

```bash
cd /Volumes/KINGSTON/projects/finRAG/backend
python3 -m uvicorn app.main:app --reload --port 8000
```

- [ ] Call `GET /api/documents` and confirm imported documents appear.
- [ ] Run a query through `POST /api/query` or the frontend and confirm citations/reference chunks come from imported corpus content.
- [ ] If using live Bailian providers, keep `.env` local and do not commit it.

## Acceptance Criteria

- `documents.json`, `chunks.json`, `bm25_index.json`, and `vector_index.json` are regenerated.
- `GET /api/documents` returns imported document titles and chunk counts.
- Backend query retrieval can find imported chunks.
- Frontend does not require redesign; it consumes existing APIs.
