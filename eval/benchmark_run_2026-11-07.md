# Phase 3 benchmark run — 2026-11-07

## Run provenance

- Questions: revised `eval/questions.csv`, 25 questions (q01–q25).
- Structural gold-set validator: passed locally against the 37-document manifest.
- Database: packaged Chroma database at `dist/PolicyLens/PolicyLens Data/chroma_db`.
- Collections/strategies: fixed-size (5,973 chunks) and structure-aware (14,157 chunks).
- Retrieval depth: top 10.
- Model loading completed; the only emitted PyTorch message was the informational macOS distributed-redirect warning.
- Output files generated locally: `eval/retrieval_log_phase3.csv`, `eval/metrics_phase3.csv`, `eval/run_metadata_phase3.json`.
- Raw retrieval log, metrics, run metadata, per-question results, disagreements, and selected ranked-passage evidence are committed on this branch.

## Overall results

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Questions | 25 | 25 |
| Indexed chunks | 5,973 | 14,157 |
| Recall@3 | 0.52 | 0.56 |
| Recall@5 | 0.56 | 0.68 |
| Recall@10 | 0.76 | 0.76 |
| MRR | 0.527762 | 0.558667 |

Structure-aware chunking has a modest overall lead in Recall@3, Recall@5, and MRR. Recall@10 is tied. It uses approximately 2.37 times as many chunks (14,157 / 5,973). Query latency is measured per query across 25 questions per strategy: fixed-size median 2.648 ms, p95 4.808 ms; structure-aware median 2.318 ms, p95 3.104 ms. These figures cover the Chroma search call only and exclude model loading and query embedding. Current local packaged Chroma database footprint: 259 MB total (224 MB `chroma.sqlite3`, plus two collection segment directories of 25 MB and 9.9 MB). Per-collection attribution is pending segment-to-collection mapping; these sizes are from the current local database, not a per-strategy allocation yet.

Packaged ingestion log (2026-11-07): 37 manifest documents; 33 ingested, 4 skipped, 0 failed, 0 missing; 4,670 pages processed; 216 OCR pages; 5,320 fixed-size chunks; 12,920 structure-aware chunks; elapsed time 897.46 seconds (14 min 57 sec). This log is distinct from the later 1.92-second unchanged rerun and from earlier November 3 logs.

The later packaged rerun (2026-11-07) reports 0 ingested, 37 skipped, 0 failed, 0 missing in 1.92 seconds, supporting idempotent unchanged-source handling.

The packaged corpus directory is `dist/PolicyLens/PolicyLens Data/corpus/pdfs` and contains 37 PDFs. Total PDF directory size has not yet been measured.

## Table-question subset

Denominator: 5 questions.

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Recall@3 | 0.40 | 0.80 |
| Recall@5 | 0.40 | 0.80 |
| Recall@10 | 0.80 | 0.80 |
| MRR | 0.453571 | 0.800000 |

Structure-aware chunking performs substantially better at early ranks on this small table-labelled subset. This is consistent with preserving table/section context, but does not prove that chunk structure alone caused the difference.

## Paraphrased-question subset

Denominator: 5 questions.

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Recall@3 | 0.60 | 0.40 |
| Recall@5 | 0.60 | 0.40 |
| Recall@10 | 1.00 | 0.60 |
| MRR | 0.653571 | 0.433333 |

Fixed-size chunking performs better on the five paraphrased questions. This is an important counter-signal against selecting structure-aware chunking solely on its overall mean.

## Comparison with the earlier baseline

The earlier 25-question benchmark (before the recent gold-set edits) recorded:

| Metric | Earlier fixed | Earlier structure |
|---|---:|---:|
| Recall@3 | 0.40 | 0.64 |
| Recall@5 | 0.44 | 0.72 |
| Recall@10 | 0.64 | 0.80 |
| MRR | 0.414825 | 0.590667 |

The latest run uses revised q02/q03 wording and page ranges, so the two runs are not a strictly paired comparison of an unchanged gold set. The new results must be treated as the current baseline. Do not attribute the metric changes to chunking or code changes without a per-question comparison and verified gold labels.

## Preliminary interpretation

- Structure-aware leads modestly overall on early retrieval and MRR; Recall@10 is tied.
- Structure-aware is notably stronger on the table-labelled subset.
- Fixed-size is notably stronger on the paraphrased subset.
- Structure-aware has 2.37x the indexed chunks, so database footprint and latency matter to the final choice.
- The gold set is only 25 questions, concentrated in a small number of RBI documents, and was not a blind holdout.
- These are retrieval-layer results, not answer accuracy or regulatory-compliance guarantees.

## Remaining work before Phase 3 closure

The benchmark, raw retrieval outputs, per-question analysis, selected disagreement evidence, and revised q04/q17/q13 interpretation are committed. The remaining work is validation and operational evidence:

1. Complete the exact local-corpus PDF page-alignment review for all 25 gold references and record corrections in `gold_set_review.md`.
2. Confirm the five table questions genuinely depend on table values and the five paraphrased questions are materially paraphrased.
3. Complete or explicitly disposition the four visual checks (S03, S05, S06, S07). The documented concerns include S03's distorted multiplier and S05/S07's table layout/association.
4. Add one source-linked before/after cleaning example.
5. OCR accuracy remains unmeasured. Either test a representative scanned page against a manually transcribed reference or explicitly retain OCR accuracy as an unmeasured limitation for this phase.
6. Record fixed-size and structure-aware Chroma directory sizes, packaged ingestion elapsed time, total pages processed, and rerun/skip/failure behaviour.
7. Update the evaluation report with the final limitations and a chunking recommendation that considers retrieval quality, index footprint, and measured latency.

Per-strategy query latency is already recorded above (median/p95: fixed-size 2.648/4.808 ms; structure-aware 2.318/3.104 ms). The raw retrieval log, metrics, run metadata, per-question results, disagreements, and selected evidence are already committed; these are not outstanding tasks.

Phase 3 remains open until the remaining evidence is completed or each item is explicitly accepted as a documented limitation with an agreed scope.
