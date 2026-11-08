# Phase 4 demo and evidence capture

This runbook captures the current PolicyLens state without rebuilding or modifying the index.

## 1. Export index evidence (read-only)

Use the packaged database that was evaluated for Phase 3:

```bash
python eval/export_index_evidence.py \
  --db-path "dist/PolicyLens/PolicyLens Data/chroma_db"
```

The script writes:
- `evidence/index_snapshot/index_summary.json`
- `evidence/index_snapshot/policylens_v1_fixed_sample.json`
- `evidence/index_snapshot/policylens_v1_structure_sample.json`

The summary includes live collection counts and five representative records per collection, including metadata and a 200-character passage preview. It performs read-only Chroma operations. Expected counts for the evaluated snapshot are 5,973 fixed-size and 14,157 structure-aware chunks. If your local packaged database reports different counts, do not edit the output to force these expected values; investigate whether it is the same benchmark snapshot.

Capture a screenshot of the summary and one sample JSON record with `doc_id`, `title`, `issuer`, `page_start`, `page_end`, `section_title`, and `source_hash` visible.

## 2. Show ingestion and idempotency evidence

Do not rerun full ingestion just to make a demo. The committed November 7 run record documents the full 37-document run (33 ingested, 4 skipped, 0 failed, 0 missing) and the unchanged rerun (37 skipped, 0 failed, 0 missing, 1.92 seconds).

For the recording, open:
- `eval/benchmark_run_2026-11-07.md`
- the matching full-ingestion and unchanged-rerun logs in `logs/`

Show the final run summaries, making clear that the second run was an unchanged-source rerun rather than a second full ingestion.

## 3. Demonstrate filtered retrieval

Use the verified q04 query from the Phase 3 gold set:

```bash
python search.py "How should the beneficial owner of a legal person be identified?" \
  --strategy structure --top_k 5 --filter issuer=RBI \
  --db-path "dist/PolicyLens/PolicyLens Data/chroma_db"
```

The verified live run returned the expected KYC Direction passage on page 38 at rank 1 (score 0.7235), under section "Part IV - Identification of Beneficial Owner". The RBI filter resolved to `Reserve Bank of India`. The full observed output is recorded in [VERIFIED_SEARCH_EXAMPLE.md](VERIFIED_SEARCH_EXAMPLE.md). This uses the existing index; it does not ingest or alter documents.

Do not use the earlier KYC-documents or cash-disbursement queries as success examples: their live top results did not directly answer the query.

## 4. Verify the source page

For q04, open the PDF corresponding to `rbi_kyc_2024` under `data/pdfs/` in Preview and navigate to PDF page 38. Show the original page alongside the CLI result so the audience can verify provenance. The search output and gold-set match establish retrieval alignment; the original PDF should still be shown in the demo. Do not claim legal interpretation or semantic correctness beyond what the page visibly supports.

## 5. Screenshot status and capture requirements

Seven historical screenshots are present in `evidence/screenshots/`. Two are known stale:
- `02_corpus_overview.png` shows old collection counts (2,691 fixed and 2,423 structure-aware).
- `07_test_results.png` shows an old five-test run; the latest verified run is 21 passed.

Do not present those two images as current evidence. Do not overwrite them until genuine replacement captures have been reviewed. The remaining five historical screenshots have not been revalidated against the current state.

Required current captures:
1. Search UI with a query and result showing title, page range and section.
2. Corpus overview with the current evaluated collection counts (5,973 fixed and 14,157 structure-aware), clearly labelled as benchmark index counts.
3. Index evidence JSON showing a sample record's required metadata.
4. Ingestion log summary for the 37-document full run.
5. Unchanged rerun summary (37 skipped, zero failures/missing).
6. Filtered CLI search and the matching source PDF page (use q04; see section 3).
7. Current test output (`21 passed`, from the latest verified run).

The index JSON exports and `VERIFIED_SEARCH_EXAMPLE.md` are committed evidence, but they are not substitutes for a requested screenshot or video. Actual screenshots of the local Streamlit UI, Terminal, Preview, and test run must be captured on the Mac. Keep the historical images until each replacement has been captured and checked.

## 6. Three-minute demo sequence

- 0:00–0:35 — Explain the pipeline and show the recorded full ingestion summary.
- 0:35–0:55 — Show the unchanged rerun and explain hash-based skipping.
- 0:55–1:35 — Run the filtered CLI search.
- 1:35–2:20 — Open the returned PDF and verify the page range/section.
- 2:20–2:45 — Show the two collection counts and one sample metadata record.
- 2:45–3:00 — State the retrieval-only scope and key limitations: OCR accuracy unmeasured; table fidelity needs source-page verification; the evaluation set is small and RBI-concentrated.

## Submission caution

The November 7 benchmark counts (5,973 and 14,157) are not the same as the full-ingestion run's chunk counters (5,320 and 12,920). Keep those measurements labelled by run and purpose. Do not present an older screenshot's counts as the final index snapshot.
