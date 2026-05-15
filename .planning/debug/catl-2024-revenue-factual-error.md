---
status: investigating
trigger: "Investigate issue: catl-2024-revenue-factual-error"
created: 2026-05-15T00:00:00+08:00
updated: 2026-05-15T00:22:00+08:00
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: CONFIRMED — table fact extraction misassigns headers/units, and retrieval/rerank amplifies corrupted facts via fiscal-year fallback and same-score ordering
test: completed targeted JSON/code inspection and exact query table-fact retrieval
expecting: diagnose-only response with root cause, confidence, fix plan, and proposed tests
next_action: return ROOT CAUSE FOUND report

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: Answer should use 300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf page 9 table with 2024 revenue 362,012,554 千元, 2023 revenue 400,917,045 千元, YoY -9.70%.
actual: Rerank Top5 includes misleading table_fact candidates with wrong labels/periods/units; generated answer picks 400.92 亿元 as 2024 revenue and says 2023 / YoY unavailable.
errors: No exception; factual error in retrieval evidence and answer.
reproduction: Ask “宁德时代 2024 年营业收入是多少？同比变化如何？” in the chat UI.
started: Occurs after table-aware retrieval/table_facts integration; user screenshot shows current UI behavior.

## Eliminated
<!-- APPEND only - prevents re-investigating -->

## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-05-15T00:03:00+08:00
  checked: debug knowledge base and required file presence
  found: no knowledge-base entry was present/readable; required source and processed JSON files exist; chunks.json is 42MB and table_facts.json is 1.4MB
  implication: no prior known pattern shortcut; investigation must compare extracted facts against code paths and source chunks
- timestamp: 2026-05-15T00:10:00+08:00
  checked: processed table_facts.json for CATL values 362,012,554 / 400,917,045 / 222,629,450
  found: correct page 9 facts exist with 2024年=362,012,554 and 2023年=400,917,045, but unit is CNY despite metric label saying 千元; multiple later-table facts mislabel 400,917,045 as 2024年 or 2024年度 and include 222,629,450 as 2024年度; units are also CNY
  implication: extraction has confirmed metadata corruption for period and unit; retrieval/generation can be misled even before LLM reasoning
- timestamp: 2026-05-15T00:15:00+08:00
  checked: raw table artifacts for pages 9, 19, 119, 121
  found: page 19 headers put 2024年 at column 3 and 2023年 at column 7 while numeric cells are columns 2 and 6; page 119/121 headers put 2024年度 at column 2 and 2023年度 at column 4 while numeric cells are columns 1 and 3; extractor uses numeric cell index directly against header index, causing right-shifted period assignment
  implication: primary extraction bug is table-header alignment when parsed rows contain blank leading/interstitial cells not aligned with header columns
- timestamp: 2026-05-15T00:17:00+08:00
  checked: query_table_facts output for exact query
  found: top 5 table fact hits were 2022/2023 page 9 facts admitted via fiscal_year:2024 source-name fallback, corrupted page 19 400,917,045 as 2024年, then correct page 9 362,012,554 as 2024年; all scored 10.7
  implication: retrieval ranking is a contributing bug; explicit requested year should not be satisfied by FY2024 source name when fact period says a different concrete year
- timestamp: 2026-05-15T00:19:00+08:00
  checked: hybrid and rerank boosting
  found: hybrid injects top table facts as evidence text with unit and period from corrupted metadata; rerank gives strong boosts to strict_period_match and period_label 2024年/2024年度, so corrupted facts are promoted rather than penalized
  implication: rerank/generation are downstream amplifiers; LLM prompt is not the origin but lacks conflict-resolution/unit-normalization guardrails
- timestamp: 2026-05-15T00:21:00+08:00
  checked: table row chunks for same pages
  found: row chunks preserve full rows including correct values and YoY on page 9, but metadata unit remains CNY and later pages render as Column 2/4 without mapped period headers
  implication: row chunks contain enough raw evidence for a human/LLM to answer, but structured metadata is unreliable and conflicts with raw row content

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: Primary root cause is table fact extraction in backend/app/core/ingestion/table_facts.py using numeric row cell indexes directly as header indexes despite PDF table rows containing blank spacer/label cells. This shifts period labels for CATL page 19/119/121 facts, e.g. 400,917,045 becomes period 2024年/2024年度 instead of 2023, and 222,629,450 becomes 2024年度 instead of 2023年度. Unit inference also collapses amount scale into currency, recording CNY instead of CNY thousands/千元. Secondary root cause is retrieval/rerank accepting FY2024 source filename as a strict 2024 match even when fact period_label is 2022年/2023年/column_N, and then boosting corrupted table_fact candidates. Prompt/generation consumes these misleading evidence lines; it is not the originating fault.
fix: Diagnose-only. Proposed fix is to repair header-to-value alignment and unit-scale extraction, require period_label compatibility over source FY fallback for explicit-year questions, prefer annual summary/page 9/table rows with YoY for annual revenue questions, and add prompt guardrails for conflicting facts/units.
verification: Not applied; diagnosis confirmed by exact processed JSON records, raw table artifacts, query_table_facts output, and code inspection.
files_changed: []
