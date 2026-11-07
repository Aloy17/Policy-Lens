# Phase 3 — Retrieval evaluation

## Purpose and scope

This evaluation compares fixed-size and structure-aware chunking on the same 25-question gold set, embedding model, Chroma collections, and retrieval depth. A result is relevant only when its `doc_id` equals the gold document and its inclusive page range overlaps the gold page range. This is a retrieval-layer evaluation; it does not evaluate answer generation.

The current question set has five table questions and five paraphrased questions. The KYC source metadata has been corrected to the 2016 issue date and 2025-08-14 consolidation date while retaining the legacy `rbi_kyc_2024` ID for index compatibility. q16–q20 have been checked against the official FPI annex; q21–q24 have been checked against the official 2022 Digital Lending notification; q25 has been narrowed to the commercial-bank audited-return row. The remaining KYC page references and all local PDF page alignment still require a final validation pass. Do not present the evaluation as fully gold-validated yet.

## Run against the packaged index

From the repository root, with the packaged app database present:

```bash
PYTHONPATH=. python eval/evaluate.py \
  --db-path "dist/PolicyLens/PolicyLens Data/chroma_db" \
  --collection policylens_v1 \
  --questions eval/questions.csv \
  --top-k 10 \
  --output eval/retrieval_log_phase3.csv
PYTHONPATH=. python eval/analyze_results.py \
  --log eval/retrieval_log_phase3.csv \
  --questions eval/questions.csv
```

The evaluator loads the model configured in `config.yaml`. The database override is intentional: the packaged app's index is separate from the source-mode default `chroma_db/`. Do not point this run at the source-mode database unless it has been populated with the matching `policylens_v1_fixed` and `policylens_v1_structure` collections.

Outputs:
- `retrieval_log_phase3.csv`: ranked results, gold-hit labels, scores, and query latency.
- `metrics_phase3.csv`: overall and labelled-subset Recall@3/5/10 and MRR.
- `run_metadata_phase3.json`: DB path, collection counts, model/config, machine/runtime details, and latency summary.
- `per_question_phase3.csv`: first relevant rank and hit flags per strategy.
- `disagreements_phase3.csv`: questions where top-1 document or Recall@10 outcome differs.
- `selected_disagreement_evidence.csv`: ranked passage previews for q04, q17, and q13, exported for report review.

Historical `retrieval_log.csv`, `retrieval_log_final.csv`, `metrics.csv`, and `disagreements.csv` are retained as historical outputs and are not overwritten.

## Selected disagreement evidence

After the Phase 3 evaluation and disagreement analysis, export the three report examples with their retrieved passage previews:

```bash
PYTHONPATH=. python eval/inspect_disagreements.py
```

The default cases are q04 (beneficial-owner identification), q17 (FPI table proof-of-address requirement), and q13 (KYC/AML-CFT staff training). The output contains each strategy's ranked document, page range, section, score, gold-hit flag, latency, and 200-character retrieved preview. This is evidence extraction, not a causal explanation: inspect the full source PDF pages and chunk text before attributing an outcome to chunking or table handling.

## Metric definitions

- Recall@k here is the proportion of questions with at least one gold-document chunk overlapping a gold page in the top k.
- Reciprocal rank is (1/r), where (r) is the first rank satisfying the gold document and page-overlap rule; it is zero when no result in the retrieved top 10 matches.
- MRR is the mean reciprocal rank over all questions in the evaluated subset.
- The two chunking strategies are compared with identical queries and index/model settings. Query latency measures the Chroma search call only; it excludes model loading and query embedding time.

## Required manual validation before reporting

1. Complete the local PDF page-alignment pass for every gold reference in `questions.csv`; confirm the cited content is present on the specified page range. Record any correction and reason in `gold_set_review.md`. Official source-text checks are documented there, but they do not replace checking the exact local corpus files.
2. Confirm that exactly five questions genuinely require table values and exactly five are materially paraphrased from source wording. A label count alone does not prove category quality.
3. Inspect the three most informative strategy disagreements. Explain the retrieved content and page evidence, not merely the rank difference.
4. Inspect ten deterministically sampled PDF pages using `sample_inspection_pages.py`; record extraction/OCR/table/layout quality in `manual_inspection_template.csv`.
5. Capture before/after cleaning for one page and estimate OCR word accuracy on an image-backed page using a manually transcribed reference sample.
6. Record ingestion elapsed time and total pages from the actual packaged run; record database directory size and machine/runtime metadata. Local embedding API charges are zero; local compute is not cost-free.
7. Treat the 2022 Digital Lending Guidelines as a historical circular: RBI's later Digital Lending Directions, 2025 supersede the earlier framework. Do not imply the 2022 circular is current policy.

## Interpretation limits

The gold set currently concentrates on three RBI documents, rather than representing all 37 corpus documents. It was assembled after ingestion work began, so it is not a fully blind holdout. The fixed-vs-structure result is conditional on this question set and current parser/chunker/index settings. It is not evidence of universal superiority or production compliance coverage.


## Export the sampled pages for inspection

After pulling the latest branch and generating the deterministic sample template, export the ten sampled pages into a single review bundle. This reads the local PDFs and does not change the source files or sampling template.

```bash
PYTHONPATH=. python eval/export_sampled_pages.py --pdf-dir "dist/PolicyLens/PolicyLens Data/PDFs"
```

Replace the `--pdf-dir` value if your local corpus PDFs are stored elsewhere. The directory must contain files named `<doc_id>.pdf`, matching `data/manifest.csv`.

The helper creates a new `eval/manual_inspection/` directory containing:

- `inspection_report.md`: native extracted text, OCR text when OCR is run, and cleaned text for each sampled page, alongside extraction/layout metadata.
- `inspection_metadata.csv`: page dimensions, text-block and image counts, estimated image coverage, table count, word counts, and OCR triage status.
- `sampled_pages_review.pdf`: the original sampled PDF pages combined in sample order for visual inspection.

OCR is run only on sampled pages that meet the same text-density/image-coverage triage thresholds configured for ingestion (20-word minimum; 50% image coverage with fewer than 120 words). Use `--no-ocr` to inspect native extraction only. OCR candidacy is a heuristic and does not establish OCR accuracy. The script does not estimate OCR word accuracy; that requires manually comparing OCR output with a human-transcribed reference.

The PDF review bundle copies the original pages, preserving their vector/text content. The report's printed-page hint is tentative and must be checked visually. After reviewing the bundle, complete the corresponding human-judgment fields in `manual_inspection_template.csv`; do not infer table completeness, reading-order correctness, or legitimate-text loss from metadata alone.
