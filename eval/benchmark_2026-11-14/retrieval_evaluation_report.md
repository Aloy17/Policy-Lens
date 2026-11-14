# Retrieval evaluation report — 2026-11-14

## Executive summary

The benchmark completed successfully against the repaired local Chroma collections. It compared fixed-size and structure-aware retrieval on 41 valid gold questions. Structure-aware retrieval scored higher on the page-overlap metrics, while the lexical evidence proxy was mixed. All paired-bootstrap 95% confidence intervals include zero, so this run does **not** establish a statistically conclusive winner.

The benchmark is limited: the gold set covers only 7 of 37 corpus documents and is heavily weighted toward the RBI KYC Direction. The two relevance measures are retrieval proxies, not semantic answer-quality evaluation.

**Recommendation:** retain both chunking strategies as viable pending broader gold-set coverage and source-verified qualitative review. Do not select a corpus-wide winner from this run alone.

## Dataset validation

The v2 gold set contains 42 questions:

- 41 valid questions included in the headline benchmark.
- 1 question excluded because its label was invalid.
- Structural validation passed.
- PDF evidence validation passed for all valid evidence rows; no checks were skipped.
- Gold questions cover 7 of the 37 corpus documents.

The set includes direct, paraphrased, clause-specific, table-dependent, numerical/date, distinction, and multi-passage questions. Coverage is nevertheless uneven: RBI KYC accounts for 25 questions, Digital Lending 7, DPDP Rules 5, and four other documents one question each. Results should not be generalized to the full corpus.

## Benchmark configuration and integrity

| Setting | Value |
|---|---|
| Embedding model | `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` |
| Fixed-size collection | `policylens_v1_fixed` — 5,932 records |
| Structure-aware collection | `policylens_v1_structure` — 15,773 records |
| Headline questions | 41 |
| Retrieval depth | top-k = 10 |
| Distance metric | Cosine distance (lower is closer) |
| Metadata filter | None |
| Query embeddings | One shared set reused for both strategies |
| Benchmark database | Temporary copy of the local Chroma database |

Integrity checks passed:

- All 41 valid questions returned results.
- No malformed result arrays and no empty-result questions.
- The benchmark opened a temporary copy.
- The original database tree hash was identical before and after the run.
- `database_unmodified` was `true`.

The run metadata records Python 3.13.14, Chroma 1.5.9, sentence-transformers 6.2.0, and macOS 27.2.1 arm64. Machine-specific absolute paths are intentionally omitted.

## Aggregate retrieval results

The table reports the `headline_all_valid` subset. Values are proportions except MRR.

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Page-overlap MRR | 0.4978 | 0.5983 |
| Page-overlap Hit@3 | 0.5122 | 0.6341 |
| Page-overlap Recall@3 | 0.5041 | 0.6138 |
| Page-overlap Precision@3 | 0.2520 | 0.3089 |
| Page-overlap Hit@5 | 0.6585 | 0.7073 |
| Page-overlap Recall@5 | 0.6504 | 0.6870 |
| Page-overlap Precision@5 | 0.2098 | 0.2195 |
| Page-overlap Hit@10 | 0.7805 | 0.8293 |
| Page-overlap Recall@10 | 0.7805 | 0.8089 |
| Page-overlap Precision@10 | 0.1317 | 0.1439 |
| Lexical proxy MRR | 0.2542 | 0.2834 |
| Lexical proxy Hit@3 | 0.2439 | 0.2927 |
| Lexical proxy Recall@3 | 0.2236 | 0.2846 |
| Lexical proxy Precision@3 | 0.0894 | 0.1057 |
| Lexical proxy Hit@5 | 0.3415 | 0.3171 |
| Lexical proxy Recall@5 | 0.3333 | 0.3089 |
| Lexical proxy Precision@5 | 0.0780 | 0.0683 |
| Lexical proxy Hit@10 | 0.4634 | 0.4146 |
| Lexical proxy Recall@10 | 0.4634 | 0.3943 |
| Lexical proxy Precision@10 | 0.0537 | 0.0463 |

### Metric interpretation

- **Page-overlap proxy:** a retrieved chunk is considered relevant when its document ID matches and its inclusive page range overlaps a gold passage. This is a broad location signal; a chunk on the right page can still contain the wrong clause.
- **Passage-term lexical proxy:** applies page overlap and requires all terms in a gold passage's `passage_terms` group to occur in the retrieved chunk. Each gold passage is evaluated independently. This is stricter, but remains lexical rather than semantic validation.
- **Hit Rate@k:** whether at least one relevant result appears in the top k.
- **Recall@k:** fraction of gold passages covered in the top k.
- **Precision@k:** relevant results divided by k; k remains the denominator even when fewer than k results are returned.
- **MRR:** mean reciprocal rank of the first relevant result.

Structure-aware retrieval leads on every listed page-overlap aggregate. The lexical proxy is mixed: structure-aware leads at MRR and top-3, while fixed-size leads at Hit@5, Hit@10, Recall@10, and the corresponding top-5/top-10 precision values. This divergence reinforces that page overlap alone overstates evidence quality.

## Paired bootstrap comparison

The run used 10,000 paired bootstrap iterations with seed 0. Differences below are structure-aware minus fixed-size.

| Metric | Difference | 95% confidence interval |
|---|---:|---:|
| Page-overlap RR | +0.1004 | [-0.0273, +0.2303] |
| Page-overlap Hit@10 | +0.0488 | [-0.0732, +0.1951] |
| Page-overlap Recall@10 | +0.0285 | [-0.1098, +0.1707] |
| Page-overlap Precision@5 | +0.0098 | [-0.0439, +0.0634] |
| Lexical evidence RR | +0.0292 | [-0.0827, +0.1372] |
| Lexical evidence Hit@10 | -0.0488 | [-0.1707, +0.0732] |
| Lexical evidence Recall@10 | -0.0691 | [-0.1951, +0.0528] |
| Lexical evidence Precision@5 | -0.0098 | [-0.0390, +0.0195] |

Every interval includes zero. The observed direction and magnitude are descriptive for this sample; they are not evidence of a statistically established winner.

## Initial case inspection

The benchmark's generated inspection notes identified these representative outcomes:

| Question | Fixed-size observation | Structure-aware observation | Initial interpretation |
|---|---|---|---|
| q03 | Relevant RBI KYC material at rank 2 | Top 3 were unrelated SEBI material | Fixed-size appears better on this query |
| q04 | Expected passage missed in top 3 | RBI KYC page 38 at rank 1 | Structure-aware appears better |
| q07 | Relevant result at rank 1 | Relevant result at rank 1 | Both succeed under page-overlap inspection |
| q08 | Relevant result at rank 1 | Relevant result at rank 1 | Both succeed under page-overlap inspection |
| q09 | Top 3 mostly relevant | Top 2 relevant | Both retrieve relevant material |
| q16 | Relevant material around pages 93–94 at rank 3 | Top 3 reported as irrelevant | Fixed-size has a page-overlap hit; the expected table evidence still needs direct verification |
| x03 | Similar but incorrect SEBI research-analyst material | Generic investor-complaint headings from multiple documents | Neither strategy found the expected page 10 evidence |

**Evidence boundary:** these observations are from the benchmark's generated case inspection and the result snippets/page labels previously examined. The full local `retrieval_log.csv`, complete retrieved chunk text, and corresponding original PDF pages were not available in the repository during preparation of this report. Therefore, the observations above are not represented as source-PDF-verified findings. In particular, q16's table correctness and the exact clause-level correctness of q03/q04/q07/q08/q09 remain unconfirmed here. A source-verified qualitative error analysis is still required before treating Task 1 as fully complete.

## Retrieved-chunk qualitative inspection

A follow-up inspection was completed using selected chunk records pasted from the local Chroma database. This verifies the supplied extracted chunk text, but it is not visual verification against the original PDF page images. The supplied extract omitted question IDs and ranks for each record, so it cannot independently reconstruct the complete top-k ordering; case/rank associations below retain the benchmark inspection notes.

| Question | Content-level finding from supplied chunks |
|---|---|
| q03 | Fixed-size chunk on pp. 22–24 contains the operative third-party CDD reliance conditions, including immediate access to CDD records, availability of supporting documentation without delay, third-party regulation and controls, high-risk-jurisdiction restriction, and the RE's ultimate responsibility. Strong substantive evidence. |
| q04 | Structure-aware chunk on p. 38 contains only the heading “Part IV - Identification of Beneficial Owner”; it does not contain the operative identification test. This is a page-overlap false positive, not an answer-supporting hit. |
| q07 | Structure-aware chunk on pp. 57–58 explicitly states the CKYCR upload deadline is within 10 days of commencement of the account-based relationship. Strong substantive evidence. The corresponding fixed-size chunk was not included in the supplied extract. |
| q08 | Structure-aware chunk on pp. 58–59 explicitly says the RE must retrieve the updated KYC record from CKYCR and update its own record. Strong substantive evidence. The corresponding fixed-size chunk was not included in the supplied extract. |
| q09 | Supplied fixed and structure-aware chunks are on-topic and refer to originator/beneficiary information and RE responsibilities, but neither excerpt enumerates all required data elements. Relevant but partial evidence; not sufficient by itself to mark a complete answer as retrieved. |
| q16 | Fixed-size chunk on pp. 93–94 contains the Annex IV table row and Category I cell marked “mandatory” for constitutive documents. Strong substantive table evidence. The corresponding structure-aware chunk was not included in the supplied extract. |
| x03 | Fixed-size chunk on pp. 31–33 contains the escalation route: if the research analyst does not satisfactorily resolve the complaint, the investor may lodge a complaint with SEBI through SCORES. It is answer-supporting evidence despite being outside the gold page 10. The structure-aware chunk on p. 3 contains only the heading “Investor Complaints” and is insufficient. |

This inspection demonstrates two important evaluation issues: page overlap can count heading-only chunks as hits (q04), while strict gold-page matching can miss answer-supporting evidence elsewhere in the same source document (x03). q09 also shows why a binary page hit cannot establish answer completeness.

**Remaining limits:** only selected chunks were supplied, not every top-k result for both strategies; the paste omitted query IDs and ranks; q07/q08 fixed-size counterparts and q16 structure-aware counterpart were not included; original PDF page images were not supplied. Accordingly, this is a partial content-level inspection, not a complete source-PDF-verified qualitative evaluation.

See [qualitative_error_analysis.md](qualitative_error_analysis.md) for the detailed chunk-by-chunk notes and evidence boundaries.

## Limitations

1. **Corpus coverage:** 7 of 37 documents; RBI KYC dominates the set.
2. **Small sample:** 41 questions produce wide confidence intervals.
3. **Non-blind set:** questions were authored after ingestion work began; this is not a blind holdout.
4. **Proxy relevance:** page overlap can reward the wrong clause on the right page. Passage-term matching reduces but does not eliminate this problem.
5. **Limited multi-passage coverage:** only three valid questions require multiple passages.
6. **No answer-generation evaluation:** this experiment measures retrieval, not whether a generated answer is correct, complete, or properly cited.
7. **Qualitative review partial:** selected retrieved chunk text has been inspected; complete top-k reconstruction and visual source-PDF verification remain outstanding.

## Conclusion and next work

This run shows a consistent page-overlap advantage for structure-aware chunking, but the lexical evidence proxy does not agree consistently and the paired bootstrap does not establish a significant difference. There is not enough evidence to declare either strategy superior.

Before final sign-off:

1. If full sign-off requires visual source-PDF verification, inspect the original PDF page images and complete top-k records for the representative cases.
2. Expand the gold set across more of the 37-document corpus, especially documents currently absent or underrepresented.
3. Add end-to-end answer and citation evaluation separately; do not conflate it with retrieval metrics.

## Reproducibility

The benchmark runner and gold-set validator are in this branch. The benchmark was run locally against the audited Chroma database; raw run artifacts remain local and are not committed here because the metadata contains machine-specific paths and the retrieval log can be large.

See [README.md](README.md) for methodology, metric definitions, validation and reproduction commands.
