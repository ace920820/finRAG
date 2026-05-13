---
phase: 01-backend-foundation-and-demo-data
plan: 02
subsystem: demo-data
tags: [fixtures, documents-api, seed-data]
key-files:
  - backend/app/core/ingestion/fixture_loader.py
  - backend/app/core/ingestion/normalizer.py
  - backend/app/data/processed/documents.json
  - backend/app/data/processed/chunks.json
  - backend/app/data/processed/demo_cases.json
  - backend/scripts/seed_data.py
  - backend/scripts/build_index.py
  - backend/app/api/documents.py
metrics:
  documents: 4
  chunks: 7
  demo_cases: 3
---

# Plan 02 Summary: Demo Data And Documents API

## Completed

- Added fixture loader and normalizer helpers.
- Added deterministic processed fixture data for Moutai, CATL, a research report, and macro/news context.
- Added all three required demo questions to `demo_cases.json`.
- Added seed and fixture-only build scripts.
- Wired `GET /api/documents` to fixture-backed metadata with chunk counts.

## Deviations

- A transient nested `backend/backend/` path was created during execution and cleaned up before final validation.

## Self-Check

PASSED — fixture scripts run and `/api/documents` returns 4 documents.
