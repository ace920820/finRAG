# finRAG demo public data sourcing summary — PDF-only revision

Retrieved/revised at: 2026-05-13

## Scope and source policy
Prepared PDF-only demo documents for 贵州茅台、宁德时代、英伟达/NVIDIA、台积电/TSMC. Sources are public/legal access points only: CNINFO, NVIDIA Investor Relations/Q4CDN, TWSE MOPS/doc.twse.com.tw, DBS public PDFs, and Eastmoney-hosted public research PDFs. No login, paywall, CAPTCHA/Cloudflare bypass, or paid research database scraping was used.

## Output locations
- PDF source documents: `data/docs/source_documents/**/*.pdf`
- CSV manifest: `data/manifest/finrag_demo_public_docs_manifest.csv`
- JSON manifest: `data/manifest/finrag_demo_public_docs_manifest.json`
- Download/source gap log: `data/manifest/finrag_demo_public_docs_failures.json`
- Non-PDF cleanup notes: `data/manifest/finrag_demo_non_pdf_source_entries.json`

## Counts
- Total manifest PDF documents: 40
- By company: {"台积电": 10, "宁德时代": 10, "英伟达": 10, "贵州茅台": 10}
- By doc_type: {"annual_financial_statement": 2, "annual_report": 8, "quarterly_report": 20, "research_report": 4, "semiannual_report": 6}
- Non-PDF files remaining under source_documents: 0
- Gaps/failures recorded: 2

## Classification
- 财报/公告/filings: `annual_report`, `semiannual_report`, `quarterly_report`, plus TSMC `annual_financial_statement`, all under `financial_reports/`.
- 研报: `research_report` under `research_reports/`. Copyright remains with original publishers; keep for internal demo/RAG evaluation only and do not redistribute.

## Coverage notes / gaps
- A 股: CNINFO PDFs cover 2024Q1, 2024H1, 2024Q3, FY2024, 2025Q1, 2025H1, 2025Q3, FY2025, 2026Q1 for 贵州茅台 and 宁德时代. A 股 H1/annual reports cover Q2/Q4 periods; no separate Q2/Q4 quarterly PDF is normally published.
- NVIDIA: official investor/Q4CDN PDF versions of 10-K/10-Q are used instead of SEC HTML.
- TSMC: TWSE/MOPS PDF financial statements and FY2024 annual report are used. Official TSMC IR PDFs that trigger Cloudflare challenge were recorded in the failure/source log and were not bypassed.

## Recommended RAG ingest glob
```bash
/Volumes/KINGSTON/projects/finRAG/data/docs/source_documents/**/*.pdf
```

For metadata-aware ingest, load `data/manifest/finrag_demo_public_docs_manifest.csv` and attach `company`, `ticker`, `doc_type`, `period`, `publish_date`, `source_url`, and `license/access_note` to chunks.

## File list
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_annual_report_FY2024_2025-03-15_cninfo.pdf` (2,070,073 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_annual_report_FY2025_2026-03-10_cninfo.pdf` (2,043,710 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_quarterly_report_2024Q1_2024-04-16_cninfo.pdf` (325,466 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_quarterly_report_2024Q3_2024-10-19_cninfo.pdf` (380,288 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_quarterly_report_2025Q1_2025-04-15_cninfo.pdf` (335,963 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_quarterly_report_2025Q3_2025-10-21_cninfo.pdf` (351,045 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_quarterly_report_2026Q1_2026-04-16_cninfo.pdf` (537,170 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_semiannual_report_2024H1_2024-07-27_cninfo.pdf` (1,684,794 bytes)
- `data/docs/source_documents/catl/financial_reports/300750SZ_catl_semiannual_report_2025H1_2025-07-31_cninfo.pdf` (1,590,151 bytes)
- `data/docs/source_documents/catl/research_reports/300750SZ_catl_research_report_2026-04-17_dfcfw_bocom.pdf` (375,409 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_annual_report_FY2024_2025-04-03_cninfo.pdf` (3,626,217 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_annual_report_FY2025_2026-04-17_cninfo.pdf` (1,082,847 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_quarterly_report_2024Q1_2024-04-27_cninfo.pdf` (380,443 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_quarterly_report_2024Q3_2024-10-26_cninfo.pdf` (511,257 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_quarterly_report_2025Q1_2025-04-30_cninfo.pdf` (154,608 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_quarterly_report_2025Q3_2025-10-30_cninfo.pdf` (186,470 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_quarterly_report_2026Q1_2026-04-25_cninfo.pdf` (158,374 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_semiannual_report_2024H1_2024-08-09_cninfo.pdf` (3,058,620 bytes)
- `data/docs/source_documents/moutai/financial_reports/600519SH_moutai_semiannual_report_2025H1_2025-08-13_cninfo.pdf` (805,855 bytes)
- `data/docs/source_documents/moutai/research_reports/600519SH_moutai_research_report_2026-04-26_dfcfw_dongwu.pdf` (552,698 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10k_FY2024_2024-02-21_q4cdn.pdf` (1,074,533 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10k_FY2025_2025-02-26_q4cdn.pdf` (1,274,715 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10k_FY2026_2026-02-25_q4cdn.pdf` (1,048,995 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10q_FY2025Q1_2024-05-29_q4cdn.pdf` (1,010,273 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10q_FY2025Q2_2024-08-28_q4cdn.pdf` (708,766 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10q_FY2025Q3_2024-11-20_q4cdn.pdf` (504,010 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10q_FY2026Q1_2025-05-28_q4cdn.pdf` (375,056 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10q_FY2026Q2_2025-08-27_q4cdn.pdf` (555,385 bytes)
- `data/docs/source_documents/nvidia/financial_reports/NVDA_nvidia_10q_FY2026Q3_2025-11-19_q4cdn.pdf` (424,904 bytes)
- `data/docs/source_documents/nvidia/research_reports/NVDA_nvidia_research_report_2026-01-08_dbs.pdf` (227,406 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_annual_financial_statement_FY2024_2025-02-27_twse_mops_en.pdf` (3,975,227 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_annual_financial_statement_FY2025_2026-02-26_twse_mops_en.pdf` (3,990,599 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_annual_report_FY2024_2025-05-02_twse_mops_en.pdf` (9,339,330 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_financial_statement_2024Q1_2024-05-15_twse_mops_en.pdf` (2,834,231 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_financial_statement_2024Q3_2024-11-14_twse_mops_en.pdf` (4,475,896 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_financial_statement_2025Q1_2025-05-15_twse_mops_en.pdf` (2,444,179 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_financial_statement_2025Q3_2025-11-14_twse_mops_en.pdf` (1,917,922 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_semiannual_financial_statement_2024H1_2024-08-14_twse_mops_en.pdf` (3,595,386 bytes)
- `data/docs/source_documents/tsmc/financial_reports/TSM_tsmc_semiannual_financial_statement_2025H1_2025-08-14_twse_mops_en.pdf` (3,206,052 bytes)
- `data/docs/source_documents/tsmc/research_reports/TSM_tsmc_research_report_2026_dbs.pdf` (257,899 bytes)
