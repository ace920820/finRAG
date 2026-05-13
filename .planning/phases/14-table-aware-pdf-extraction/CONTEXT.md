# Phase 14 Context — Table-Aware PDF Extraction

Source requirement: `docs/table处理.txt`.

Goal: extend the PDF/raw extraction stage so table content is preserved as structured artifacts instead of only plain text.

Key constraints:
- Existing text extraction and raw Markdown output must continue to work.
- No OCR in this phase.
- Prefer low-cost demo-suitable tools first: `pdfplumber` and/or `pymupdf4llm`.
- Extraction failure for tables should degrade to text-only and never break the corpus import.
