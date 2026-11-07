# Phase 3 benchmark run — 2026-11-07

## Run provenance

- Questions: revised `eval/questions.csv`, 25 questions (q01–q25).
- Structural gold-set validator: passed locally against the 37-document manifest.
- Database: packaged Chroma database at `dist/PolicyLens/PolicyLens Data/chroma_db`.
- Collections/strategies: fixed-size (5,973 chunks) and structure-aware (14,157 chunks).
- Retrieval depth: top 10.
- Model loading completed; the only emitted PyTorch message was the informational macOS distributed-redirect warning.
- Output files generated locally: `eval/retrieval_log_phase3.csv`, `eval/metrics_phase3.csv`, `eval/run_metadata_phase3.json`.
- The raw log, metrics CSV, and metadata JSON still need to be committed from the local run so the benchmark is reproducible from the repository.

## Overall results

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Questions | 25 | 25 |
| Indexed chunks | 5,973 | 14,157 |
| Recall@3 | 0.52 | 0.56 |
| Recall@5 | 0.56 | 0.68 |
| Recall@10 | 0.76 | 0.76 |
| MRR | 0.527762 | 0.558667 |

Structure-aware chunking has a modest overall lead in Recall@3, Recall@5, and MRR. Recall@10 is tied. It uses approximately 2.37 times as many chunks (14,157 / 5,973), which must be considered alongside index size and latency before making a final operational recommendation.

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

## Still required before Phase 3 closure

1. Run `eval/analyze_results.py` on the newly generated local retrieval log and commit its per-question and disagreement outputs.
2. Inspect the latest selected disagreements using full retrieved passages and source PDFs; the earlier q04/q17/q13 analysis predates this revised benchmark and should not be reused without checking.
3. Commit the raw retrieval log, metrics, run metadata, and analysis outputs from this run.
4. Complete the local PDF page-alignment review for all 25 gold references.
5. Complete the four outstanding visual checks (S03, S05, S06, S07), including the distorted S03 multiplier and table association/layout concerns.
6. Record a before/after cleaning example.
7. OCR accuracy remains unmeasured: the ten sampled pages were all native-text pages and did not trigger OCR. A representative scanned page and manual transcription are required for an accuracy estimate.
8. Record database directory size, median/p95 latency, and packaged ingestion timing evidence.

Phase 3 remains open until the evidence above is either completed or explicitly reported as an assignment limitation with an agreed disposition.
