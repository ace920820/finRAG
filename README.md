# finRAG

FinRAG is a local financial RAG demo with a FastAPI backend, React frontend, and a repeatable document ingestion pipeline.

## Document Import Pipeline

Canonical raw data location:

```text
backend/app/data/raw/
  extracted/<collection-name>/*.md
  manual/<collection-name>/*.{md,txt}
  _meta/*.json
```

### 1. Extract PDFs into raw Markdown

```bash
cd pdf2md
python3 -m elite_daily_pdf_to_md.cli \
  --profile finrag \
  --source-dir "/path/to/source-pdfs" \
  --raw-root "/Volumes/KINGSTON/projects/finRAG/backend/app/data/raw" \
  --collection-name "research-reports" \
  --extractor pymupdf
```

Manual Markdown/text supplements can be placed under:

```text
backend/app/data/raw/manual/research-reports/
```

### 2. Import raw Markdown/text into processed JSON

```bash
cd backend
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name research-reports \
  --processed-dir app/data/processed
```

This writes `documents.json` and `chunks.json` using the existing backend schemas.

### 3. Rebuild retrieval indexes

```bash
cd backend
python3 scripts/build_index.py \
  --processed-dir app/data/processed \
  --index-dir app/data/index
```

Or import and rebuild in one step:

```bash
cd backend
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name research-reports \
  --processed-dir app/data/processed \
  --index-dir app/data/index \
  --rebuild-index
```

After import and index build, existing `GET /api/documents` and `POST /api/query` use the imported corpus without frontend redesign.

No `.env` or Alibaba Bailian API key is required for importer tests. Keep local `.env` files out of git.
