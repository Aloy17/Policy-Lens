# Task 3 review progress

Last updated: 2026-11-16. Status: merged into `main`.

## Completed

- Answer key: 41 valid questions (q01-q37, x01-x04), all marked verified against their cited source passages.
- Evidence review: all 820 retrieved chunks reviewed and annotated (41 questions × 2 strategies × 10 ranks). Every row has an evidence class, supported fact IDs where applicable, citation status, source-verification status, and review notes.
- Corrected the q04 structure rank-1 false positive: it was a heading-only paragraph 34 passage and did not support the beneficial-owner facts.
- Source-page matching: all 820 citation ranges were checked against the supplied 570-page source-text export. All 54 original pages flagged for visual review were inspected in the 18 committed contact sheets; every citation row is now source-verified.
- Validation logic was reproduced against the current answer key and review CSV: 41 questions, 820 review rows, no schema errors, no unknown fact IDs, and no accurate citation marked source-unverified.
- Scoring: `answer_validation_scores.csv` contains 82 question-strategy results.

## Final reviewed retrieval results

| Metric | Fixed 500-token chunks | Structure-aware chunks |
| --- | ---: | ---: |
| Complete support | 19 / 41 | 25 / 41 |
| Partial support | 5 / 41 | 5 / 41 |
| No required-fact support in top 10 | 17 / 41 | 11 / 41 |
| Mean required-fact coverage | 53.3% | 67.2% |

Across both strategies, 44 of 82 question-strategy pairs achieved complete fact coverage, 10 partial coverage, and 28 no required-fact coverage in the top 10. Structure-aware retrieval has higher aggregate fact coverage in this reviewed set. These are descriptive results for this dataset and these retrieval settings, not a general claim about all corpora.

## Citation and source verification

- 820 citation assessments were eligible for accuracy scoring; all 820 were accurate against the supplied source-page text export and visual page checks where flagged (100%).
- All 820 evidence rows now have `source_verified=yes`; no citation remains excluded from the accuracy denominator.
- The 18 visual-review contact sheets cover 108 PDF pages (54 label/source-page pairs). All 54 original source pages flagged for visual review were inspected.
- The scanned Special Bearer Bonds Ordinance passage (x04), PDF page 2, was visually checked; section 3 is legible and the citation is source-verified. The instrument bears a handwritten repeal note, so its legal currency is not established by this retrieval evaluation.
- PFRDA VCIP (q34), PDF page 6, was visually checked; para 3.26 is legible and the direct definition citation is source-verified.

## Currency and interpretation limitations

- The RBI Digital Lending circular used for q21-q24 and q31-q33 is explicitly marked repealed and replaced by the RBI (Digital Lending) Directions, 2025. Scores for those questions measure retrieval against the historical 2022 source specified in the answer key; they must not be presented as current regulatory guidance.
- All flagged source pages have been visually confirmed; q34 and x04 are called out above because they were key evidence examples.
- x03's gold passage was updated to the 2026 SEBI Research Analysts Master Circular (pp.69–70). The current passage specifies SCORES 2.0, the current platform URL, two-level RAASB/SEBI review, and the physical-complaint route. The older scores.gov.in URL and helpline are retained only as historical retrieval evidence, not as current facts.
- Text alignment and semantic relevance are separate: matching page ranges do not by themselves prove that a passage supports an answer. The evidence classes and supported fact IDs are the human semantic annotations.

## Release status

- Task 3 evidence review, source verification, validation, and scoring are complete.
- Task 3 changes are merged into the repository's `main` branch; no Task 3 merge or release gate remains open.
- Local validation passed: 41 questions and 820 review rows, with no schema or fact-ID errors.
- Local scoring passed: 82 question-strategy scores generated.
- GitHub Actions passed on commit `d562196` for the full test suite, selected-page extraction fidelity, and OCR accuracy. This records the successful run at that commit; it does not claim a fresh workflow run on every later documentation/evidence-only commit.

## Review boundary

This evaluation is a retrieval-evidence assessment, not legal advice and not a certification that every cited instrument is current. In particular, the superseded digital-lending circular and the handwritten repeal note on the 1981 Ordinance must remain explicit limitations in any final report.
