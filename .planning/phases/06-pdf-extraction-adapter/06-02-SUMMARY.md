---
phase: 06-pdf-extraction-adapter
plan: 02
subsystem: adapter-docs-validation
tags: [docs, validation, uat]
key-files:
  - pdf2md/README.md
  - .planning/phases/06-pdf-extraction-adapter/06-VALIDATION.md
  - .planning/phases/06-pdf-extraction-adapter/06-UAT.md
  - .planning/REQUIREMENTS.md
  - .planning/STATE.md
metrics:
  full-pdf2md-tests: 70 passed
---

# Plan 06-02 Summary: Adapter Documentation And Validation

## Completed

- Documented FinRAG extraction mode in `pdf2md/README.md`.
- Documented the Phase 7 raw artifact contract: extracted Markdown plus Markdown/JSON manifests.
- Updated Phase 6 validation evidence with concrete commands and results.
- Added manual UAT checklist for add-PDF, extract, inspect metadata, rerun skip, force, and failure cases.
- Marked only Phase 6 `PDF-*` requirements complete; Phase 7 import/index requirements remain pending.

## Deviations

- No frontend or FinRAG schema import code was changed because Phase 6 is extraction-only.

## Self-Check

PASSED — `cd pdf2md && python3 -m pytest`.
