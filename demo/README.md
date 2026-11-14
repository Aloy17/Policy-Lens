# PolicyLens demo

The brief asks for a 3 minute video or screenshots covering ingestion, a filtered search, and a cited page. A video has not been recorded. Screenshots covering each step are committed; the shot-by-shot script for recording a video is in [`evidence/PHASE4_DEMO_RUNBOOK.md`](../evidence/PHASE4_DEMO_RUNBOOK.md).

| Step | Evidence |
|---|---|
| Ingest (full run, 33 ingested, 4 skipped, 0 failed) | `evidence/screenshots/09_ingestion_and_idempotency_summary.png`, raw log `evidence/ingestion_logs/run1_full.log` |
| Second run, nothing re-ingested (37 skipped) | same screenshot, raw log `evidence/ingestion_logs/run2_rerun.log` |
| Index contents and metadata | `evidence/screenshots/11_index_sample_current.png`, `evidence/index_snapshot/` |
| Filtered search with title, pages, section | `evidence/screenshots/13_q04_retrieval_source_verification.png`, `evidence/VERIFIED_SEARCH_EXAMPLE.md` |
| Cited page check | open `rbi_kyc_2024` PDF page 38 (the q04 gold page) and compare with the top search result |

Screenshot 13 shows the CLI result (KYC Direction, page 38, rank 1); it does not include the PDF page itself. Add a capture of page 38 next to it if you want the cited-page step shown in one frame.

Suggested 3 minute video order: run `ingest.py` (or show the skip run), run `search.py "How should the beneficial owner of a legal person be identified?" --filter issuer=RBI`, then open page 38 of the source PDF.
