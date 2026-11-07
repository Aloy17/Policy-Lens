# PolicyLens evaluation report — working outline

> Status: measured retrieval benchmark and revised selected-disagreement analysis are committed. Gold-page audit, visual parsing checks, before/after cleaning evidence, and efficiency measurements remain incomplete or explicitly unmeasured.

## 1. Executive summary
- Evaluation objective: compare fixed-size and structure-aware chunking for retrieval over the PolicyLens corpus.
- Corpus: 37 documents in the manifest; confirm final ingestion snapshot before publication.
- Evaluation set: 25 questions (q01–q25); five table-labelled and five paraphrased questions.
- Main result (2026-11-07): fixed-size Recall@3/5/10 = 0.52/0.56/0.76, MRR = 0.527762; structure-aware = 0.56/0.68/0.76, MRR = 0.558667.
- Subset signal: structure-aware leads on table questions; fixed-size leads on paraphrased questions (n=5 each).
- Selected disagreement review: q04 and q17 favour structure-aware; q13 favours fixed-size. See `eval/disagreement_analysis.md`.
- A final operational recommendation remains pending index disk footprint and packaged-ingestion measurements; per-strategy query latency is now available.

## 2. System and corpus
- Ingestion architecture: PyMuPDF parsing, table extraction, OCR triage, cleaning, two chunking strategies, local sentence-transformer embeddings, Chroma.
- Corpus composition: 37 manifest documents; add document types, issuers, page counts, and scanned/mixed share from the final manifest.
- Versions and configuration: Python, package versions, embedding model, Chroma version, chunk sizes/overlap, collection names.
- Index evidence: benchmark collections contain 5,973 fixed-size and 14,157 structure-aware chunks. The current packaged Chroma database occupies 259 MB total (224 MB SQLite file plus segment directories of 25 MB and 9.9 MB); per-collection disk attribution is pending.

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
| Indexed chunks | 5,973 | 14,157 |

- Table subset (n=5): fixed Recall@3/5/10 = 0.40/0.40/0.80, MRR 0.453571; structure-aware = 0.80/0.80/0.80, MRR 0.800000.
- Paraphrased subset (n=5): fixed = 0.60/0.60/1.00, MRR 0.653571; structure-aware = 0.40/0.40/0.60, MRR 0.433333.
- Structure-aware has about 2.37x as many indexed chunks. Per-strategy Chroma search latency (25 queries each): fixed-size median/p95 2.648/4.808 ms; structure-aware 2.318/3.104 ms. These exclude query embedding and model loading. Index disk sizes remain to be measured.

## 5. Disagreement analysis
- Revised ranked evidence for q04, q17, q13 is documented in `eval/disagreement_analysis.md`.
- q04: structure-aware gold hit rank 1; fixed-size no gold hit in top 10.
- q17: structure-aware gold hit rank 1 (and table result rank 3); fixed-size first gold hit rank 8.
- q13: fixed-size gold hit rank 5; structure-aware no gold hit in top 10.
- Do not infer a causal mechanism from rank differences or short previews alone.

## 6. Parsing and data quality
- Ten-page deterministic sample: seed 2026, 10 pages from a 5,050-page PDF sampling frame.
- Findings in `eval/manual_inspection_findings.md`: native extraction on all 10 pages; table numeric fidelity and layout/reading-order risks observed.
- Visual verification of S03, S05, S06, and S07 remains pending; do not describe the page-level findings as visually confirmed.
- OCR was not run on the sample; OCR word accuracy is **not measured**. A separate manually transcribed scan test is required for an accuracy estimate.
- Before/after cleaning example with source-page provenance remains to be added.

## 7. Efficiency, robustness, and scaling
- Packaged ingestion log (2026-11-07): 37 documents in manifest; 33 ingested, 4 skipped, 0 failed/missing; 4,670 pages, 216 OCR pages; 5,320 fixed-size and 12,920 structure-aware chunks; 897.46 seconds total (about 14 min 57 sec). A later unchanged rerun skipped all 37 documents in 1.92 seconds. These ingestion counts are from the packaged ingestion log and should not be conflated with the retrieval benchmark's indexed chunk counts.
- Current combined Chroma database footprint: 259 MB (224 MB SQLite plus two segment directories of 25 MB and 9.9 MB); per-collection attribution remains pending.
- Per-strategy Chroma search latency is measured (median/p95: fixed-size 2.648/4.808 ms; structure-aware 2.318/3.104 ms), excluding query embedding and model loading.
- Embedding/API cost: local Sentence Transformers inference; no hosted embedding API charge for this benchmark.
- Idempotent rerun evidence: 37 unchanged documents skipped in 1.92 seconds, with zero failures or missing documents.
- Failed/skipped document handling and rerun behavior.
- Scaling to 100,000 documents: batching, incremental ingestion, metadata filters, persistence/backup, monitoring, and operational bottlenecks.

## 8. Security, privacy, and regulatory freshness
- Access control and document-level authorization approach.
- Data minimization, local processing, retention, and audit logging.
- Superseded circular handling: version metadata, effective dates, repeal/supersession links, and retrieval filtering so historical text is not represented as current policy.
- Explicitly identify the 2016 KYC Master Direction (August 14, 2025 consolidation) and 2022 Digital Lending Guidelines as historical source snapshots where applicable.

## 9. Conclusion and future work
- Evidence-based chunking recommendation after footprint/latency trade-offs.
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
