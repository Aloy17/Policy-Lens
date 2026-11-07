# Phase 3 — Retrieval evaluation

## Purpose and scope

This evaluation compares fixed-size and structure-aware chunking on the same 25-question gold set, embedding model, Chroma collections, and retrieval depth. A result is relevant only when its `doc_id` equals the gold document and its inclusive page range overlaps the gold page range. This is a retrieval-layer evaluation; it does not evaluate answer generation.

The current question set has exactly five records marked as table questions and five marked as paraphrased. The paraphrase labels and gold page references are **provisional until checked against the exact local PDF pages**. Do not present the evaluation as fully gold-validated before that review.

## Run against the packaged index

From the repository root, with the packaged app database present:

```bash
python eval/evaluate.py \
  --db-path "dist/PolicyLens/PolicyLens Data/chroma_db" \
  --collection policylens_v1 \
  --questions eval/questions.csv \
  --top-k 10 \
  --output eval/retrieval_log_phase3.csv
python eval/analyze_results.py \
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

Historical `retrieval_log.csv`, `retrieval_log_final.csv`, `metrics.csv`, and `disagreements.csv` are retained as historical outputs and are not overwritten.

## Metric definitions

- Recall@k here is the proportion of questions with at least one gold-document chunk overlapping a gold page in the top k.
- Reciprocal rank is (1/r), where (r) is the first rank satisfying the gold document and page-overlap rule; it is zero when no result in the retrieved top 10 matches.
- MRR is the mean reciprocal rank over all questions in the evaluated subset.
- The two chunking strategies are compared with identical queries and index/model settings. Query latency measures the Chroma search call only; it excludes model loading and query embedding time.

## Required manual validation before reporting

1. Open every gold PDF/page in `questions.csv`; confirm the cited content is present on the specified page range. Record any correction and reason in `gold_set_review.md`.
2. Confirm that exactly five questions genuinely require table values and exactly five are materially paraphrased from source wording. A label count alone does not prove category quality.
3. Inspect the three most informative strategy disagreements. Explain the retrieved content and page evidence, not merely the rank difference.
4. Inspect ten deterministically sampled PDF pages using `sample_inspection_pages.py`; record extraction/OCR/table/layout quality in `manual_inspection_template.csv`.
5. Capture before/after cleaning for one page and estimate OCR word accuracy on an image-backed page using a manually transcribed reference sample.
6. Record ingestion elapsed time and total pages from the actual packaged run; record database directory size and machine/runtime metadata. Local embedding API charges are zero; local compute is not cost-free.
7. Treat the 2022 Digital Lending Guidelines as a historical circular: RBI's later Digital Lending Directions, 2025 supersede the earlier framework. Do not imply the 2022 circular is current policy.

## Interpretation limits

The gold set currently concentrates on three RBI documents, rather than representing all 37 corpus documents. It was assembled after ingestion work began, so it is not a fully blind holdout. The fixed-vs-structure result is conditional on this question set and current parser/chunker/index settings. It is not evidence of universal superiority or production compliance coverage.
