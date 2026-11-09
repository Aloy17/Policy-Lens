# Phase 4 Evidence Status

**Last reviewed:** 2026-11-09  
**Purpose:** Inventory the evidence retained for the current PolicyLens submission.

## Current submission evidence

- Six-page report: `report/PolicyLens_Report.pdf`.
- Index snapshot exports: `evidence/index_snapshot/index_summary.json`, `policylens_v1_fixed_sample.json`, and `policylens_v1_structure_sample.json`.
- Evaluated index counts: 5,973 fixed-size chunks and 14,157 structure-aware chunks.
- Verified filtered q04 retrieval: KYC Direction page 38 at rank 1, score 0.7235; observed output in `evidence/VERIFIED_SEARCH_EXAMPLE.md`.
- Full-ingestion and unchanged-rerun run record: `evidence/ingestion_logs/2026-11-07_ingestion_and_idempotency.log`.
- Latest recorded automated validation: gold-set validator passed; pytest 21 passed.
- Six current screenshots:
  - `08_corpus_overview_current.png`
  - `09_ingestion_and_idempotency_summary.png`
  - `10_search_interface_current.png`
  - `11_index_sample_current.png`
  - `12_test_results_current.png`
  - `13_q04_retrieval_source_verification.png`

The screenshots exist and their pixel dimensions were checked. Their visual contents have not been independently inspected in this review; legibility and required visible fields still need final presentation review.

## Ingestion and idempotency

The committed November 7 run record documents:

- Full run: 37 manifest documents; 33 ingested, 4 skipped, 0 failed, 0 missing; 4,670 pages; 216 OCR pages; 5,320 fixed-size chunks; 12,920 structure-aware chunks; 897.46 seconds.
- Unchanged-source rerun: 0 ingested, 37 skipped, 0 failed, 0 missing; 1.92 seconds.

Screenshot 09 is a screenshot of the documented run summary, not an original raw terminal capture. The committed run record is the retained ingestion evidence. Do not describe the screenshot as a raw log.

## Remaining verification work

- Visually review screenshots 08–13 for legibility and correct content.
- Confirm screenshot 13 visibly pairs the q04 CLI result with the original `rbi_kyc_2024` PDF page 38.
- If the rubric requires raw terminal captures specifically, recover the original November 7 raw logs if available. Do not fabricate or relabel the run record as raw output.

The index JSON files are machine-readable exports. `VERIFIED_SEARCH_EXAMPLE.md` is a Markdown record of observed CLI output, not a screenshot.

## Demo readiness

The q04 query is the recommended live retrieval demonstration. It returned the expected gold page at rank 1 with the correct document and section. The three-minute sequence is documented in `PHASE4_DEMO_RUNBOOK.md`.
