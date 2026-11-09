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

Current screenshot: `evidence/screenshots/08_corpus_overview_current.png`.  
Current sample-record screenshot: `evidence/screenshots/11_index_sample_current.png`.

The sample record should show `doc_id`, `title`, `issuer`, `page_start`, `page_end`, `section_title`, and `source_hash`. Review the screenshot for legibility before submission.

## 2. Show ingestion and idempotency evidence

Do not rerun full ingestion just to make a demo. The committed November 7 run record documents the full 37-document run (33 ingested, 4 skipped, 0 failed, 0 missing) and the unchanged rerun (0 ingested, 37 skipped, 0 failed, 0 missing, 1.92 seconds).

The full run processed 4,670 pages (216 OCR pages), produced 5,320 fixed-size and 12,920 structure-aware chunks, and took 897.46 seconds (14 min 57 sec). The unchanged-source rerun took 1.92 seconds.

Current screenshot: `evidence/screenshots/09_ingestion_and_idempotency_summary.png`. This is a screenshot of the documented benchmark run summary, **not an original raw terminal ingestion-log capture**. The committed November 7 run record is the retained ingestion evidence. Do not substitute unrelated run output or describe the summary screenshot as a raw log. If original November 7 raw logs are recovered, preserve them separately and update this status.

## 3. Demonstrate filtered retrieval

Use the verified q04 query from the Phase 3 gold set:

```bash
python search.py "How should the beneficial owner of a legal person be identified?" \
  --strategy structure --top_k 5 --filter issuer=RBI \
  --db-path "dist/PolicyLens/PolicyLens Data/chroma_db"
```

The verified live run returned the expected KYC Direction passage on page 38 at rank 1 (score 0.7235), under section "Part IV - Identification of Beneficial Owner". The RBI filter resolved to `Reserve Bank of India`. The full observed output is recorded in [VERIFIED_SEARCH_EXAMPLE.md](VERIFIED_SEARCH_EXAMPLE.md). This uses the existing index; it does not ingest or alter documents.

Do not use the earlier KYC-documents or cash-disbursement queries as success examples: their live top results did not directly answer the query.

Current Streamlit screenshot: `evidence/screenshots/10_search_interface_current.png`.

## 4. Verify the source page

For q04, open the PDF corresponding to `rbi_kyc_2024` under `data/pdfs/` in Preview and navigate to PDF page 38. Show the original page alongside the CLI result so the audience can verify provenance. The search output and gold-set match establish retrieval alignment; the original PDF should still be shown in the demo. Do not claim legal interpretation or semantic correctness beyond what the page visibly supports.

Current combined capture: `evidence/screenshots/13_q04_retrieval_source_verification.png`. Confirm visually that both the CLI result and original PDF page 38 are legible.

## 5. Current screenshot inventory

The current submission evidence consists of these six captures:

| File | Evidence |
|---|---|
| `08_corpus_overview_current.png` | Evaluated index counts |
| `09_ingestion_and_idempotency_summary.png` | Documented full-ingestion and unchanged-rerun summaries; not raw logs |
| `10_search_interface_current.png` | Current Streamlit search UI |
| `11_index_sample_current.png` | Structure-aware sample metadata |
| `12_test_results_current.png` | Current recorded pytest output: 21 passed, 5 warnings |
| `13_q04_retrieval_source_verification.png` | q04 CLI result alongside source PDF page 38 |

The six files exist and their pixel dimensions were checked. Their visual contents still need a final legibility/content review.

## 6. Three-minute demo sequence

- 0:00–0:35 — Explain the pipeline and show the documented full-ingestion summary.
- 0:35–0:55 — Show the unchanged rerun and explain hash-based skipping.
- 0:55–1:35 — Run the filtered CLI search.
- 1:35–2:20 — Open the returned PDF and verify the page range/section.
- 2:20–2:45 — Show the two collection counts and one sample metadata record.
- 2:45–3:00 — State the retrieval-only scope and key limitations: OCR accuracy unmeasured; table fidelity needs source-page verification; the evaluation set is small and RBI-concentrated.

## Submission caution

The November 7 benchmark counts (5,973 and 14,157) are not the same as the full-ingestion run's chunk counters (5,320 and 12,920). Keep those measurements labelled by run and purpose. Do not present an older screenshot's counts as the final index snapshot.
