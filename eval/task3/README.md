# Task 3 — End-to-end answer-support validation

## Scope and architecture boundary

PolicyLens is a **retrieval-only** application. It does not generate natural-language answers. Task 3 therefore evaluates whether retrieved passages provide enough verified evidence for a human to answer each question, and whether the displayed document/page citations lead to the supporting source. It does not score generated answers, entailment by an LLM, or legal correctness of model output.

The evaluation is intentionally human-in-the-loop: reviewers write a concise reference answer, decompose it into atomic required facts, inspect the retrieved chunk text against the source PDF, and annotate evidence/citation quality. The scoring script is deterministic and does not infer semantic support from keyword overlap.

## Dataset

The answer-key template is derived from the Task 1 gold set. It includes the 41 valid headline questions and excludes the row marked invalid/not-in-headline. Templates are intentionally created with `annotation_status=pending`, blank reference answers, and blank required facts. Do not score until every row has been reviewed and marked `verified`.

For each answerable question:
- `reference_answer`: concise answer grounded in the cited source, with qualifications and dates.
- `required_facts`: semicolon-separated atomic facts in `F1::description;F2::description` format. IDs must be unique within a question.
- `gold_passages`: inherited candidate page ranges from Task 1; reviewers must verify the exact source passage and correct or supplement this field if needed.
- `answerability`: `answerable` or `insufficient_source`.
- `annotation_status`: `pending` until the reference answer and facts have been checked against the PDF.

An `insufficient_source` question is a deliberate abstention case: leave reference answer and required facts blank, then mark it verified only after confirming the corpus does not contain sufficient evidence.

## Evidence review

Run the Task 1 retrieval benchmark first, producing a retrieval log with both strategies and top-10 chunks. Then create a review template:

```bash
PYTHONPATH=. python eval/answer_validation.py build-review-template \
  --log eval/benchmark_2026-11-14_run/retrieval_log.csv \
  --output eval/task3/evidence_review.csv --top-k 10
```

For every row, reviewers inspect the complete retrieved chunk and its source PDF page(s), then fill:
- `evidence_class`: `complete`, `partial`, `irrelevant`, or `insufficient`.
- `supported_fact_ids`: semicolon-separated IDs of facts actually supported by this chunk; leave blank if none.
- `citation_status`: `accurate`, `inaccurate`, `overinclusive`, `missing`, or `not_applicable`.
- `source_verified`: `yes` only after checking the source PDF page, not just the chunk metadata/text.
- `review_notes`: explain partial support, table-header dependencies, OCR uncertainty, or source-page mismatch.

Do not mark a passage complete solely because its page range overlaps a gold page. Heading-only hits are insufficient. For multi-passage questions, fact coverage is aggregated across the reviewed top-k passages; a single chunk need not contain every required fact.

## Commands

Create the 41-question answer-key template:

```bash
PYTHONPATH=. python eval/answer_validation.py build-answer-key
```

Validate annotations:

```bash
PYTHONPATH=. python eval/answer_validation.py validate \
  --answer-key eval/task3/answer_key.csv \
  --reviews eval/task3/evidence_review.csv
```

Score only after validation succeeds:

```bash
PYTHONPATH=. python eval/answer_validation.py score \
  --answer-key eval/task3/answer_key.csv \
  --reviews eval/task3/evidence_review.csv \
  --output eval/task3/answer_validation_scores.csv
```

The score file contains one row per question and strategy:
- `outcome`: complete support, partial support, no support, or supported abstention.
- `fact_coverage`: required facts supported by at least one reviewed retrieved passage / total required facts.
- `citation_accuracy`: accurate citations / all citation assessments (including inaccurate, overinclusive, and missing); not applicable rows are excluded.
- `unverified_source_chunks`: reviewed rows not checked against source PDF pages.

These are evidence-support metrics, not a claim that a generated answer is correct. Report complete-support rate, mean fact coverage, citation accuracy, and abstention performance separately for fixed and structure-aware retrieval.

## Safety and reproducibility

- All scripts operate on CSV files and do not connect to Chroma or mutate the index.
- The review template preserves retrieval rank, chunk ID, document ID, and page range so each judgement is traceable.
- Keep the raw retrieval log and completed annotations with the report.
- Do not call the source verified unless the original PDF page was inspected.
- Report the number of questions/chunks actually reviewed; do not silently treat unreviewed rows as failures or successes.
