# Phase 3 — Retrieval evaluation

## Purpose and scope

This evaluation compares fixed-size and structure-aware chunking on the same 25-question gold set, embedding model, Chroma collections, and retrieval depth. A result is relevant only when its `doc_id` equals the gold document and its inclusive page range overlaps the gold page range. This is a retrieval-layer evaluation; it does not evaluate answer generation.

The current question set has five table questions and five materially paraphrased questions. A structured semantic/category audit of all 25 questions is recorded in `gold_set_review.md`; the three document IDs and all inclusive page ranges pass manifest-bound checks. Official-source content checks cover q01–q25, including the FPI annex, Digital Lending notification, and commercial-bank filing row. The structural validator confirms IDs, document references, category counts, and page-range bounds; it does not establish exact local-corpus PDF page alignment. Accordingly, report the benchmark as structurally validated with explicit gold-label and extraction limitations, not as fully semantically gold-validated.

## Validate the gold-set file structure

Before running retrieval evaluation, validate the CSV schema, ordered IDs, required category counts, document IDs against the manifest, and inclusive page ranges against each document's manifest page count:

```bash
PYTHONPATH=. python eval/validate_gold_set.py
```

This checks structure and catches page ranges that exceed the manifest's declared PDF page count. It does **not** prove that a passage appears on the labelled page, validate source correctness, or assess table-question/paraphrase quality; those still require manual review.

The validator has focused regression tests covering a valid 25-question set, a page range beyond the manifest page count, and an incorrect table-question count. Run them with:

```bash
pytest -q tests/test_gold_set_validation.py
```

A lightweight GitHub Actions workflow at `.github/workflows/evaluation-validation.yml` runs these checks on pushes and pull requests that change the gold set, manifest, validator, tests, or workflow itself. It installs only `pytest`; it does not install the retrieval stack or access the local packaged Chroma database.

## Run against the packaged index

From the repository root, with the packaged app database present:

```bash
PYTHONPATH=. python eval/evaluate.py \
  --db-path "dist/PolicyLens/PolicyLens Data/chroma_db" \
  --collection policylens_v1 \
  --questions eval/questions.csv \
  --top-k 10 \
  --output eval/retrieval_log.csv
PYTHONPATH=. python eval/analyze_results.py \
  --log eval/retrieval_log.csv \
  --questions eval/questions.csv
```

The evaluator loads the model configured in `config.yaml`. The database override is intentional: the packaged app's index is separate from the source-mode default `chroma_db/`. Do not point this run at the source-mode database unless it has been populated with the matching `policylens_v1_fixed` and `policylens_v1_structure` collections.

Outputs:
- `retrieval_log.csv`: ranked results, gold-hit labels, scores, and query latency.
- `metrics.csv`: overall and labelled-subset Recall@3/5/10 and MRR.
- `rebenchmark_2026-11-07/run_metadata_phase3.json`: DB path, collection counts, model/config, machine/runtime details, and latency summary.
- `rebenchmark_2026-11-07/per_question_phase3.csv`: first relevant rank and hit flags per strategy.
- `rebenchmark_2026-11-07/disagreements_phase3.csv`: questions where top-1 document or Recall@10 outcome differs.
- `rebenchmark_2026-11-07/selected_disagreement_evidence.csv`: ranked passage previews for q04, q17, and q13, exported for report review.

The root-level `retrieval_log.csv` and `metrics.csv` contain the final November 7 benchmark. Supporting per-question, disagreement, and run-metadata exports are stored under `rebenchmark_2026-11-07/`.

## Latest benchmark snapshot (2026-11-07)

The revised 25-question gold set was evaluated locally against the packaged Chroma database. The measured results and provenance are recorded in [`benchmark_run_2026-11-07.md`](benchmark_run_2026-11-07.md). Overall structure-aware results are Recall@3 0.60, Recall@5 0.72, Recall@10 0.80, and MRR 0.578667; fixed-size results are 0.52, 0.56, 0.76, and 0.527762 respectively. Fixed-size leads on the five-question paraphrased subset. Structure-aware also has 14,157 indexed chunks versus 5,973 for fixed-size. Corrected-run query latency (median/p95: fixed-size 2.318/4.987 ms; structure-aware 2.352/2.893 ms), disagreement evidence, database footprint, and packaged-ingestion measurements are documented in the benchmark run record.

After the run, generate the current per-question and disagreement summaries:

```bash
PYTHONPATH=. python eval/analyze_results.py \\
  --log eval/retrieval_log.csv \\
  --questions eval/questions.csv
```

The 2026-11-07 benchmark report is the authoritative run record. The supporting CSV/JSON outputs are committed under `eval/rebenchmark_2026-11-07/`.

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

## Limitations retained at Phase 3 closure

1. **Exact local PDF page alignment is not fully established.** The semantic audit and official-source text checks are recorded in `gold_set_review.md`; the structural validator checks bounds, not passage-to-page truth. Treat individual gold-page labels as a documented evaluation limitation.
2. **Category review completed at the semantic level.** q16–q20 each require a table row/value or footnote; q02, q08, q14, q21, and q23 are materially paraphrased. The remaining risk is rendered table-cell fidelity, not the category count.
3. **Disagreement review completed.** q04, q17, and q13 are documented in `eval/disagreement_analysis.md`; do not infer causality from rank differences alone.
4. **Ten-page extraction sample completed.** Findings and limitations are recorded in `manual_inspection_findings.md`. Visual confirmation of S03, S05, S06, and S07 was not completed; treat the findings as extraction-output observations, not visually confirmed defects.
5. **Cleaning evidence:** a source-linked before/after example is recorded in `manual_inspection_findings.md`; this is a qualitative example, not a corpus-wide cleaning-accuracy measure.
6. **OCR accuracy is unmeasured.** The ten-page sample had no OCR candidates and OCR was not run. A separate manually transcribed scan test is needed for an accuracy estimate; otherwise report this as unmeasured.
7. **Operational measurements are complete** and recorded in `benchmark_run_2026-11-07.md`: packaged ingestion, unchanged rerun, corpus/database footprint, collection vector-segment sizes, and query latency.
8. Treat the 2022 Digital Lending Guidelines as a historical circular: RBI's later Digital Lending Directions, 2025 supersede the earlier framework. Do not imply the 2022 circular is current policy.

## Interpretation limits

The gold set currently concentrates on three RBI documents, rather than representing all 37 corpus documents. It was assembled after ingestion work began, so it is not a fully blind holdout. The fixed-vs-structure result is conditional on this question set and current parser/chunker/index settings. It is not evidence of universal superiority or production compliance coverage.


## Export the sampled pages for optional inspection

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
