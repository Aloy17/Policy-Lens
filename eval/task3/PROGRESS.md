# Task 3 review progress

Last updated: 2026-11-15. Branch: `task3-answer-key-verification`.

## Completed

- Answer key: 41 valid questions (q01-q37, x01-x04), all marked verified against their cited source passages.
- Evidence review: all 820 retrieved chunks reviewed and annotated (41 questions × 2 strategies × 10 ranks). Every row has an evidence class, supported fact IDs where applicable, citation status, source-verification status, and review notes.
- Corrected the q04 structure rank-1 false positive: it was a heading-only paragraph 34 passage and did not support the beneficial-owner facts.
- Source-page matching: citation ranges were checked against the supplied 570-page source-text export. Text-native, non-flagged page ranges are marked source-verified. Rows touching pages flagged for visual review remain source-unverified and are excluded from the citation-accuracy denominator.
- Validation logic was reproduced against the current answer key and review CSV: 41 questions, 820 review rows, no schema errors, no unknown fact IDs, and no accurate citation marked source-unverified.
- Scoring: `answer_validation_scores.csv` contains 82 question-strategy results.

## Preliminary retrieval results

| Metric | Fixed 500-token chunks | Structure-aware chunks |
| --- | ---: | ---: |
| Complete support | 18 / 41 | 25 / 41 |
| Partial support | 6 / 41 | 5 / 41 |
| No required-fact support in top 10 | 17 / 41 | 11 / 41 |
| Mean required-fact coverage | 52.7% | 67.2% |

Across both strategies, 43 of 82 question-strategy pairs achieved complete fact coverage, 11 partial coverage, and 28 no required-fact coverage in the top 10. Structure-aware retrieval has higher aggregate fact coverage in this reviewed set. These are descriptive results for this dataset and these retrieval settings, not a general claim about all corpora.

## Citation and source verification

- 698 citation assessments were eligible for accuracy scoring; all 698 were accurate against the supplied source-page text export (100%).
- 122 chunk citations still touch pages flagged for visual review and remain source-unverified; they are recorded as `not_applicable` for citation-accuracy scoring rather than being falsely counted as verified or inaccurate.
- The visual-review contact sheets cover 108 pages. Scanned/mixed pages still need page-level confirmation before any affected row can be upgraded to `source_verified=yes`.
- The scanned Special Bearer Bonds Ordinance passage (x04), PDF page 2, has now been visually checked against the committed contact sheet; section 3 is legible and the citation is marked source-verified. The instrument also bears a handwritten repeal note, so its legal currency is not established by this retrieval evaluation.
- PFRDA VCIP (q34), PDF page 6, has now been visually checked against the committed contact sheet; para 3.26 is legible and the direct definition citation is marked source-verified.

## Currency and interpretation limitations

- The RBI Digital Lending circular used for q21-q24 and q31-q33 is explicitly marked repealed and replaced by the RBI (Digital Lending) Directions, 2025. Scores for those questions measure retrieval against the historical 2022 source specified in the answer key; they must not be presented as current regulatory guidance.
- The q34 PFRDA source and x04 scanned Ordinance need visual source confirmation.
- x03 retrieved a relevant grievance passage from the 2026 SEBI Research Analysts Master Circular, while the answer key's gold passage points to an earlier circular. This is recorded as partial support pending source-version reconciliation.
- Text alignment and semantic relevance are separate: matching page ranges do not by themselves prove that a passage supports an answer. The evidence classes and supported fact IDs are the human semantic annotations.

## Remaining before Task 3 can be called fully closed

1. Complete page-level visual confirmation for the remaining 122 flagged chunk citations; q34 and x04 have been confirmed.
2. Reconcile x03's answer-key source version with the 2026 circular and decide whether to update the gold passage/reference answer.
3. Run the repository's actual local commands:
   ```bash
   ./.venv/bin/python eval/answer_validation.py validate --answer-key eval/task3/answer_key.csv --reviews eval/task3/evidence_review.csv
   ./.venv/bin/python eval/answer_validation.py score --answer-key eval/task3/answer_key.csv --reviews eval/task3/evidence_review.csv --output eval/task3/answer_validation_scores.csv
   ```
   The current score file was generated from the same scoring logic after a zero-error schema/fact-ID audit; the local run should confirm the repository implementation end-to-end.
4. Run CI on the final branch state, review the diff, and only then merge the Task 3 PR. Do not merge before the visual/source-version qualifications are resolved.

## Review boundary

This evaluation is a retrieval-evidence assessment, not legal advice and not a certification that every cited instrument is current. In particular, the superseded digital-lending circular and the handwritten repeal note on the 1981 Ordinance must remain explicit limitations in any final report.
