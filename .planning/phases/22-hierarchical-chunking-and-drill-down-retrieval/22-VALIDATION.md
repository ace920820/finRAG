---
phase: 22
slug: hierarchical-chunking-and-drill-down-retrieval
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-21
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for hierarchical chunk metadata and drill-down retrieval.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | none under `backend` |
| **Quick run command** | `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_hybrid_retrieval.py -q` |
| **Full suite command** | `cd backend && python3 -m pytest -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_hybrid_retrieval.py -q`
- **After every plan wave:** Run `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_import_pipeline_integration.py tests/test_hybrid_retrieval.py tests/test_query_api.py tests/test_kb_api.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | HIER-01, HIER-03 | T-22-01 | Hierarchy metadata remains additive and deterministic | unit/integration | `cd backend && python3 -m pytest tests/test_corpus_import.py -q` | yes | pending |
| 22-01-02 | 01 | 1 | HIER-01, HIER-03 | T-22-01 | Table row children link to table parents without leaking new paths | unit | `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_table_facts.py -q` | yes | pending |
| 22-01-03 | 01 | 1 | HIER-02, HIER-04 | T-22-02, T-22-03 | Drill-down expansion is bounded and does not pollute table-fact QA | unit | `cd backend && python3 -m pytest tests/test_hybrid_retrieval.py -q` | yes | pending |
| 22-01-04 | 01 | 1 | HIER-03, HIER-04 | T-22-01 | Persisted indexes and existing APIs remain backward compatible | integration/regression | `cd backend && python3 -m pytest tests/test_import_pipeline_integration.py tests/test_query_api.py tests/test_kb_api.py -q` | yes | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

- [ ] Extend `backend/tests/test_corpus_import.py` with deterministic section parent/child metadata assertions.
- [ ] Extend `backend/tests/test_corpus_import.py` or `backend/tests/test_table_facts.py` with table parent to table-row child linkage assertions.
- [ ] Extend `backend/tests/test_hybrid_retrieval.py` with optional drill-down retrieval coverage and table-fact regression.
- [ ] Extend index/API regression coverage only if implementation touches persisted index payload or API serialization.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have automated verify commands.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all missing references.
- [x] No watch-mode flags.
- [x] Feedback latency < 90s.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** approved 2026-05-21
