# FinRAG Backend

Local FastAPI backend for the FinRAG interview-demo MVP.

## Requirements

- Python 3.9+
- No API keys required for Phase 1

## Install

```bash
cd backend
python3 -m pip install -r requirements.txt
```

## Phase 2 provider config

Copy `backend/.env.example` to a local `.env` and fill in only your own credentials and model names.

Key fields:
- `FINRAG_MODEL_BASE_URL`
- `FINRAG_MODEL_API_KEY`
- `FINRAG_EMBEDDING_MODEL`
- `FINRAG_RERANK_MODEL`
- `FINRAG_TEXT_MODEL`

Defaults use mock providers for tests. Live Bailian smoke tests are optional and manual.

## Run

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

Base URL: `http://localhost:8000`

## Seed demo data

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

## Tests

```bash
cd backend
python3 -m pytest
```

## API surface in Phase 2

- `GET /health`
- `GET /api/documents`
- `POST /api/debug/retrieval` for development and inspection

`POST /api/query` remains a later-phase SSE workflow task.
