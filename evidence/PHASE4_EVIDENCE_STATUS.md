# Phase 4 Evidence Status

**Last reviewed:** 2026-11-08  
**Purpose:** Distinguish committed, verified evidence from historical screenshots and remaining local capture work.

## Verified and committed

- Six-page report: `report/PolicyLens_Report.pdf`.
- Index snapshot exports: `evidence/index_snapshot/index_summary.json`, `policylens_v1_fixed_sample.json`, and `policylens_v1_structure_sample.json`.
- Index counts from the evaluated snapshot: 5,973 fixed-size chunks and 14,157 structure-aware chunks.
- Verified live q04 filtered retrieval: KYC Direction page 38 at rank 1, score 0.7235; full observed output in `evidence/VERIFIED_SEARCH_EXAMPLE.md`.
- Full-ingestion and unchanged-rerun records: see `eval/benchmark_run_2026-11-07.md` and corresponding logs.
- Latest recorded automated validation: gold-set validator passed; pytest 21 passed.

## Historical screenshots requiring attention

| File | Status |
|---|---|
| `01_search_interface.png` | Historical; not revalidated against current state |
| `02_corpus_overview.png` | **Stale** — shows 2,691 fixed and 2,423 structure-aware chunks |
| `03_ingestion_results.png` | Historical; not revalidated against current state |
| `04_idempotency_test.png` | Historical; not revalidated against current state |
| `05_retrieval_comparison.png` | Historical; not revalidated against current state |
| `06_evaluation_results.png` | Historical; not revalidated against current state |
| `07_test_results.png` | **Stale** — shows 5 tests; latest verified run is 21 passed |

No historical screenshot has been overwritten.

## Remaining local capture work

The following require access to the user's running Mac desktop and cannot be truthfully generated from repository text:
1. Current Streamlit search UI screenshot.
2. Current collection overview screenshot with 5,973 / 14,157 benchmark counts.
3. Index sample JSON screenshot (the underlying JSON exports are already committed).
4. Full-ingestion log screenshot.
5. Unchanged-rerun log screenshot.
6. q04 CLI search alongside original PDF page 38.
7. Current test output screenshot showing 21 passed.

The verified search record is a Markdown evidence export, not a terminal screenshot. The index JSON files are genuine machine-readable exports. Do not label generated summaries or recreated terminal text as screenshots.

## Demo readiness

The q04 query is the recommended live retrieval demonstration. It returned the expected gold page at rank 1 with the correct document and section. The earlier KYC-document and cash-disbursement query attempts should not be presented as successful exact retrieval examples.

The three-minute demo sequence remains in `PHASE4_DEMO_RUNBOOK.md`. Phase 4 screenshot/video capture is not complete until the local captures above are made and reviewed.
