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

From the repository root, run:

```bash
python search.py "What are the KYC documents required for regulated entities?" \
  --strategy structure --top_k 5 --filter issuer=RBI
```

The CLI should display the filter and each result's title, page range, section, score, and passage preview. This uses the existing index; it does not ingest or alter documents.

## 4. Verify the source page

Take the top result's document ID and page range from the CLI output. Open the corresponding PDF under `data/pdfs/` in Preview and navigate to the returned PDF page. Show the original page alongside the CLI result so the audience can verify provenance. Do not claim the passage is semantically correct if the page itself does not support it.

## 5. Capture current screenshots

Replace the stale screenshots only after capturing the new versions and checking them:
1. Search UI with a query and result showing title, page range and section.
2. Corpus overview with the current collection counts.
3. Index evidence JSON showing a sample record's required metadata.
4. Ingestion log summary for the 37-document full run.
5. Unchanged rerun summary (37 skipped, zero failures/missing).
6. Filtered CLI search and the matching source PDF page.
7. Current test output (`21 passed`, from the latest verified run).

Do not overwrite the existing screenshots until the replacement images are confirmed. Keep the old images until then.

## 6. Three-minute demo sequence

- 0:00–0:35 — Explain the pipeline and show the recorded full ingestion summary.
- 0:35–0:55 — Show the unchanged rerun and explain hash-based skipping.
- 0:55–1:35 — Run the filtered CLI search.
- 1:35–2:20 — Open the returned PDF and verify the page range/section.
- 2:20–2:45 — Show the two collection counts and one sample metadata record.
- 2:45–3:00 — State the retrieval-only scope and key limitations: OCR accuracy unmeasured; table fidelity needs source-page verification; the evaluation set is small and RBI-concentrated.

## Submission caution

The November 7 benchmark counts (5,973 and 14,157) are not the same as the full-ingestion run's chunk counters (5,320 and 12,920). Keep those measurements labelled by run and purpose. Do not present an older screenshot's counts as the final index snapshot.
