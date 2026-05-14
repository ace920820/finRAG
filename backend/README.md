# FinRAG Backend

Local FastAPI backend for the FinRAG interview-demo MVP and document import pipeline.

## Requirements

- Python 3.9+
- API keys are optional for local tests because mock providers are the default

## Install

```bash
cd backend
python3 -m pip install -r requirements.txt
```

## Provider config

Copy `backend/.env.example` to a local `.env` and fill in only your own credentials and model names.

Key fields:
- `FINRAG_MODEL_BASE_URL`
- `FINRAG_MODEL_API_KEY` for Bailian/Qwen text generation
- `FINRAG_MODEL_API_KEY_SILICON` for SiliconFlow embedding/rerank
- `FINRAG_SILICON_BASE_URL`, default `https://api.siliconflow.cn/v1`
- `FINRAG_EMBEDDING_MODEL`
- `FINRAG_RERANK_MODEL`
- `FINRAG_TEXT_MODEL`

Defaults use mock providers for tests. Live Bailian/SiliconFlow smoke tests are optional and manual. Do not commit `.env`.

SiliconFlow embedding/rerank with Bailian Qwen text example:

```env
FINRAG_MODEL_API_KEY=your-bailian-key
FINRAG_MODEL_API_KEY_SILICON=your-siliconflow-key
FINRAG_EMBEDDING_MODEL=BAAI/bge-m3
FINRAG_RERANK_MODEL=BAAI/bge-reranker-v2-m3
FINRAG_TEXT_MODEL=qwen-plus
FINRAG_EMBEDDING_PROVIDER=silicon
FINRAG_RERANK_PROVIDER=silicon
FINRAG_TEXT_PROVIDER=bailian
```

When changing `FINRAG_EMBEDDING_PROVIDER` or `FINRAG_EMBEDDING_MODEL`, rebuild the index with the same settings before querying.

## Run

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

Base URL: `http://localhost:8000`

## Document import pipeline

Raw input location:

```text
backend/app/data/raw/
  extracted/<collection-name>/*.md
  manual/<collection-name>/*.{md,txt}
```

Use `pdf2md --profile finrag` to extract text-layer PDFs first, then run:

```bash
cd backend
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name research-reports \
  --processed-dir app/data/processed \
  --index-dir app/data/index \
  --rebuild-index
```

The importer writes:

- `app/data/processed/documents.json`
- `app/data/processed/chunks.json`
- `app/data/index/bm25_index.json`
- `app/data/index/vector_index.json`

`GET /api/documents` reflects imported documents after restart/cache refresh because it reads the same processed JSON contract. `POST /api/query` retrieves imported chunks after the index rebuild.

## Seed demo data

The demo fixture path remains available:

```bash
cd backend
python3 scripts/seed_data.py
```

## Build or validate retrieval indexes

```bash
cd backend
python3 scripts/build_index.py
```

For fixture-only validation:

```bash
cd backend
python3 scripts/build_index.py --fixture-only
```

For explicit paths:

```bash
cd backend
python3 scripts/build_index.py \
  --processed-dir app/data/processed \
  --index-dir app/data/index
```

## Tests

```bash
cd backend
python3 -m pytest
```

## API surface

- `GET /health`
- `GET /api/documents`
- `POST /api/debug/retrieval` for development and inspection
- `POST /api/preview-rewrite`
- `POST /api/query` SSE workflow
