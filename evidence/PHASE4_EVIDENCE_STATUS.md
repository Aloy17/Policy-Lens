# Phase 4 Evidence Status

**Last reviewed:** 2026-11-08  
**Purpose:** Distinguish committed evidence, current screenshots, historical screenshots, and remaining verification work.

## Verified and committed

- Six-page report: `report/PolicyLens_Report.pdf`.
- Index snapshot exports: `evidence/index_snapshot/index_summary.json`, `policylens_v1_fixed_sample.json`, and `policylens_v1_structure_sample.json`.
- Index counts from the evaluated snapshot: 5,973 fixed-size chunks and 14,157 structure-aware chunks.
- Verified live q04 filtered retrieval: KYC Direction page 38 at rank 1, score 0.7235; full observed output in `evidence/VERIFIED_SEARCH_EXAMPLE.md`.
- Full-ingestion and unchanged-rerun run summaries: `eval/benchmark_run_2026-11-07.md`.
- Latest recorded automated validation: gold-set validator passed; pytest 21 passed.
- Six current screenshots committed in commit `8ab4890`:
  - `08_corpus_overview_current.png`
  - `09_ingestion_and_idempotency_summary.png`
  - `10_search_interface_current.png`
  - `11_index_sample_current.png`
  - `12_test_results_current.png`
  - `13_q04_retrieval_source_verification.png`

The screenshots were confirmed to exist and their pixel dimensions were checked. Their visual contents have not been independently inspected in this review; confirm legibility and that each frame shows the required fields before submission.

## Ingestion evidence qualification

The November 7 full-ingestion and unchanged-rerun figures are documented in the benchmark record. Screenshot 09 is a screenshot of the documented run summary, **not an original raw ingestion-log capture**. The raw log output found under `logs/` belonged to earlier November 3 runs and must not be substituted for the November 7 run.

The documented full run: 37 manifest documents; 33 ingested, 4 skipped, 0 failed, 0 missing; 4,670 pages; 216 OCR pages; 5,320 fixed-size chunks; 12,920 structure-aware chunks; 897.46 seconds. The unchanged-source rerun: 0 ingested, 37 skipped, 0 failed, 0 missing; 1.92 seconds.

## Historical screenshots

| File | Status |
|---|---|
| `01_search_interface.png` | Historical; not revalidated against current state |
| `02_corpus_overview.png` | **Stale** — shows 2,691 fixed and 2,423 structure-aware chunks |
| `03_ingestion_results.png` | Historical; not revalidated against current state |
| `04_idempotency_test.png` | Historical; not revalidated against current state |
| `05_retrieval_comparison.png` | Historical; not revalidated against current state |
| `06_evaluation_results.png` | Historical; not revalidated against current state |
| `07_test_results.png` | **Stale** — shows 5 tests; latest verified run is 21 passed |

No historical screenshot has been overwritten. The six current captures are additional files, not replacements.

## Remaining verification work

- Visually inspect screenshots 08–13 for legibility and correct content; dimensions alone do not prove that required content is visible.
- Confirm screenshot 09 is presented as a documented summary, not as a raw log.
- Confirm screenshot 13 visibly pairs the q04 CLI result with the original `rbi_kyc_2024` PDF page 38.
- If the assignment evaluator specifically requires original raw ingestion logs rather than a documented run summary, recover the November 7 raw logs if available. Do not fabricate or relabel the benchmark record as a raw log.

The index JSON files are genuine machine-readable exports. `VERIFIED_SEARCH_EXAMPLE.md` is a Markdown record of observed CLI output, not a screenshot.

## Demo readiness

The q04 query is the recommended live retrieval demonstration. It returned the expected gold page at rank 1 with the correct document and section. The earlier KYC-document and cash-disbursement query attempts should not be presented as successful exact retrieval examples.

The three-minute demo sequence is in `PHASE4_DEMO_RUNBOOK.md`. Phase 4 capture files are now committed; final presentation review and deliverable audit remain.
