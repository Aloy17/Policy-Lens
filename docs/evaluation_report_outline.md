# PolicyLens evaluation report — working outline

> Status: working report outline. Measured retrieval results from 2026-11-07 are recorded in `eval/benchmark_run_2026-11-07.md`; gold-page audit, manual parsing checks, efficiency evidence, and refreshed disagreement analysis remain incomplete.

## 1. Executive summary
- Evaluation objective: compare fixed-size and structure-aware chunking for retrieval over the PolicyLens corpus.
- Corpus: [37 documents; verify final manifest and ingestion snapshot].
- Evaluation set: [25 questions; report final validated gold-set version].
- Main result (2026-11-07): fixed-size Recall@3/5/10 = 0.52/0.56/0.76, MRR = 0.527762; structure-aware = 0.56/0.68/0.76, MRR = 0.558667.
- Subset signal: structure-aware leads on table questions; fixed-size leads on paraphrased questions (n=5 each).
- Recommendation: defer final selection until disagreement review, index size, and latency are reconciled. See `eval/benchmark_run_2026-11-07.md`.

## 2. System and corpus
- Ingestion architecture: PyMuPDF parsing, table extraction, OCR triage, cleaning, two chunking strategies, local sentence-transformer embeddings, Chroma.
- Corpus composition: [document types, issuers, page counts, scanned/mixed share].
- Versions and configuration: [Python, package versions, embedding model, Chroma version, chunk sizes/overlap, collection names].
- Index evidence: [fixed/structure-aware chunk counts, database sizes, screenshots or reproducible exports].

## 3. Evaluation design
- Gold-set composition: 25 questions, exactly five table-dependent and five materially paraphrased questions.
- Gold relevance rule: same document ID and overlap with the inclusive gold PDF-page range.
- Retrieval depth: top 10.
- Metrics: Recall@3, Recall@5, Recall@10, MRR.
- Fairness controls: same questions, embedding model, index snapshot, retrieval depth, and runtime environment.
- Limitations: small and RBI-concentrated gold set; not a blind holdout; retrieval-layer evaluation only.

## 4. Results
| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Recall@3 | 0.52 | 0.56 |
| Recall@5 | 0.56 | 0.68 |
| Recall@10 | 0.76 | 0.76 |
| MRR | 0.527762 | 0.558667 |
| Median query latency (ms) | [ ] | [ ] |
| Index size (MB) | [ ] | [ ] |
| Indexed chunks | 5,973 | 14,157 |

Include table-question and paraphrased-subset metrics, with denominators and exact question IDs.

## 5. Disagreement analysis
For at least three representative questions:
- Question and gold source/page.
- Fixed-size top-ranked evidence and first gold hit.
- Structure-aware top-ranked evidence and first gold hit.
- Passage-level comparison and explanation grounded in the source.
- Whether the result is a genuine retrieval failure, a page-label issue, a chunk-boundary effect, or a table/reading-order issue.

Do not infer a causal mechanism from rank differences or short text previews alone.

## 6. Parsing and data quality
- Ten-page deterministic sample: sampling frame, seed, sample IDs.
- Native extraction quality and table/layout observations.
- Before/after cleaning example with source-page provenance.
- OCR candidate count and OCR word accuracy. If no representative OCR page was sampled, state that OCR accuracy was not measured and provide a separate manually transcribed scan test or explicitly mark it pending.
- Human visual-review outcomes and unresolved limitations.

## 7. Efficiency, robustness, and scaling
- Ingestion time per 100 pages; total pages and elapsed time.
- Index size and chunk counts.
- Query latency scope (state whether embedding/model loading is excluded).
- Embedding/API cost and local compute caveat.
- Idempotent rerun evidence: unchanged documents skipped, zero unintended additions/failures.
- Failed/skipped document handling and rerun behavior.
- Scaling to 100,000 documents: batching, incremental ingestion, metadata filters, persistence/backup, monitoring, and operational bottlenecks.

## 8. Security, privacy, and regulatory freshness
- Access control and document-level authorization approach.
- Data minimization, local processing, retention, and audit logging.
- Superseded circular handling: version metadata, effective dates, repeal/supersession links, and retrieval filtering so historical text is not represented as current policy.
- Explicitly identify the 2016 KYC Master Direction (August 14, 2025 consolidation) and 2022 Digital Lending Guidelines as historical source snapshots where applicable.

## 9. Conclusion and future work
- Evidence-based chunking recommendation.
- Known limitations and remediation priorities.
- Next validation and deployment steps.

## Appendix
- Gold questions and review register.
- Manifest/corpus inventory.
- Configuration and dependency versions.
- Ingestion logs, including unchanged rerun.
- Raw retrieval logs, metrics, and disagreement evidence.
- Parsing inspection template and completed human review.
- Screenshots/export evidence and demo script.
