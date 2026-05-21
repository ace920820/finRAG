---
phase: 17
slug: structured-query-understanding-and-retrieval-plan
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-21
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none under `backend`; `backend/tests/conftest.py` configures import path and mock providers |
| **Quick run command** | `cd backend && pytest tests/test_query_analysis.py tests/test_query_api.py tests/test_preview_rewrite.py -q` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~30 seconds |

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/test_query_analysis.py tests/test_query_api.py tests/test_preview_rewrite.py -q`
- **After every plan wave:** Run `cd backend && pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds for quick parser/API checks

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | QUERY-01 | T-17-01 | Parser handles arbitrary strings without network side effects or crashes | unit | `cd backend && pytest tests/test_query_analysis.py -q` | ✅ | ⬜ pending |
| 17-01-02 | 01 | 1 | QUERY-02 | T-17-02 | Optional plan serialization does not alter existing SSE event order | integration | `cd backend && pytest tests/test_query_api.py tests/test_sse_formatter.py -q` | ✅ | ⬜ pending |
| 17-01-03 | 01 | 1 | QUERY-03 | — | Demo entities and task types have canonical field assertions | unit/integration | `cd backend && pytest tests/test_query_analysis.py tests/test_query_api.py -q` | ✅ | ⬜ pending |
| 17-01-04 | 01 | 1 | QUERY-02 | — | Preview rewrite and table-aware numeric QA remain compatible | regression | `cd backend && pytest tests/test_preview_rewrite.py tests/test_query_api.py::test_query_endpoint_returns_table_fact_metadata_for_nvidia_revenue -q` | ✅ | ⬜ pending |

## Wave 0 Requirements

- [ ] `backend/tests/test_query_analysis.py` — add structured retrieval plan assertions for NVIDIA, 贵州茅台, 宁德时代, and 台积电.
- [ ] `backend/tests/test_query_api.py` — assert `query_rewrite.plan` is exposed without changing existing first-four event order.
- [ ] `backend/tests/test_schemas.py` or `backend/tests/test_sse_formatter.py` — cover optional `QueryRewriteEvent.plan` serialization.

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Sign-Off

- [x] All tasks have automated verify commands or Wave 0 dependencies.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers missing references.
- [x] No watch-mode flags.
- [x] Feedback latency < 30s for quick checks.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** approved 2026-05-21
