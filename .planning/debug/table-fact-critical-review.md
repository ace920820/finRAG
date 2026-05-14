---
status: resolved
trigger: "Investigate and fix table-aware retrieval correctness issues in FinRAG."
created: 2026-05-14T05:27:45.967247+00:00
updated: 2026-05-14T05:35:48.898676+00:00
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: K1-K4 root causes fixed in retrieval scoring/filtering and tests now use deterministic fixtures.
test: Human verifies original workflow if desired.
expecting: Table fact retrieval no longer returns percent or mismatched-year revenue facts; CI no longer needs real processed table_facts.json for these tests.
next_action: resolved after local real-query verification

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: Table fact retrieval should only boost facts for the requested company/metric/period; current-period recognition should be header/period based, not hard-coded NVIDIA column indexes; percentage values should not be returned as revenue facts; tests should not depend on or mutate real backend/app/data/processed/table_facts.json.
actual: Review reports _current_period_fact hard-codes NVIDIA Q3 column indexes; query_table_facts allows percentage values through at score threshold; hybrid table_fact supplemental score can dominate even when requested_years are present but fact years do not match; tests directly read real processed table_facts.json.
errors: Potential wrong answers for questions like “英伟达 2024 年第三季度的总营收” returning 2025/2026 facts; CI/new clone may fail without real corpus.
reproduction: Inspect backend/app/core/retrieval/table_facts.py, backend/app/core/retrieval/hybrid.py, backend/app/core/retrieval/rerank_service.py, backend/tests/test_query_api.py, backend/tests/test_table_fact_retrieval.py. Add focused fixture tests for percentage filtering and mismatched-year suppression.
started: Started after Phase 15-16 table facts / table-aware retrieval integration.

## Eliminated
<!-- APPEND only - prevents re-investigating -->


## Evidence
<!-- APPEND only - facts discovered -->


- timestamp: 2026-05-14T05:28:19.102219+00:00
  checked: backend/tests/test_table_fact_retrieval.py and backend/tests/test_query_api.py
  found: Existing tests call query_table_facts without fixture facts and API test expects corpus-derived NVIDIA raw_value 57,006.
  implication: Tests depend on real processed corpus, matching K4.

- timestamp: 2026-05-14T05:30:23.863766+00:00
  checked: backend/app/core/retrieval/table_facts.py, backend/app/core/retrieval/hybrid.py, backend/app/core/retrieval/rerank_service.py
  found: _current_period_fact lowercases metric_label but compares to capitalized set values; Q3 current period requires row_index/column_index constants; query_table_facts only downweights percent raw values and only boosts matching years, so company+metric can pass threshold without requested year match. Hybrid assigns table_fact supplemental scores around 0.55+, dominating regular RRF results; rerank applies unconditional +10 table_fact boost.
  implication: K1-K3 are confirmed wrong-data risks; fixes need hard filters for percent/raw period mismatch and query-year alignment rather than larger boosts.

- timestamp: 2026-05-14T05:33:11.683060+00:00
  checked: focused fixture tests for table_facts, hybrid fusion, and rerank alignment
  found: Before hybrid/rerank guard, mismatched FY2026 table_fact survived fusion for a 2024 query and rerank alignment boost was +20. After adding compatibility guard, focused reproductions pass.
  implication: The fix addresses K3 dominance at both fusion and rerank stages.

- timestamp: 2026-05-14T05:35:48.898676+00:00
  checked: cd backend && python3 -m pytest tests/test_table_fact_retrieval.py tests/test_hybrid_retrieval.py tests/test_rerank_service.py tests/test_query_api.py -q
  found: 18 passed, 5 warnings.
  implication: Targeted backend regression suite passes for K1-K4 fixes.

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: Table fact retrieval used soft boosts instead of hard eligibility checks: percent raw values and facts without the requested year could still cross threshold; current-period detection depended on source-name/column heuristics rather than extracted period labels; hybrid/rerank gave table_fact candidates dominant boosts even when period evidence was incompatible; tests used real processed corpus data.
fix: Added percent and requested-year filters, header/period-based current-period recognition, strict_period_match reasons, shared period compatibility guard in hybrid/rerank, and deterministic fixture tests for table facts/query API/hybrid/rerank.
verification: Real-query checks confirmed 2026 Q3 returns 57,006 first and 2024 Q3 returns 35,082 first; cd backend && python3 -m pytest tests/test_table_facts.py tests/test_table_fact_retrieval.py tests/test_query_api.py tests/test_hybrid_retrieval.py tests/test_rerank_service.py -q → 20 passed, 5 warnings.
files_changed: [backend/app/core/ingestion/table_facts.py, backend/app/core/retrieval/table_facts.py, backend/app/core/retrieval/hybrid.py, backend/app/core/retrieval/rerank_service.py, backend/tests/test_table_fact_retrieval.py, backend/tests/test_hybrid_retrieval.py, backend/tests/test_rerank_service.py, backend/tests/test_query_api.py]
