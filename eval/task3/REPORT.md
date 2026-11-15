# PolicyLens Case Study 2 — Task 3 Retrieval Evidence Evaluation

**Status:** Evidence review, visual source verification, x03 source reconciliation, scoring, local validation, and CI complete.

## 1. Scope

This evaluation compares fixed-size and structure-aware retrieval for the 41 valid headline questions in the Task 3 answer key (q01–q37 and x01–x04).

- 41 questions
- 2 retrieval strategies per question
- Top 10 chunks per strategy
- 820 retrieved chunks reviewed
- 570 source pages exported as text
- 54 source pages flagged for visual review; all 54 were inspected using the 18 committed contact sheets

The evaluator assesses human-reviewed evidence support for atomic answer facts and citation fidelity. It does not generate legal answers.

## 2. Method

For each retrieved chunk, the review records:

- Evidence class: complete, partial, irrelevant, or insufficient
- Supported required-fact IDs
- Citation status
- Whether the cited source page was verified
- A short rationale

The answer key defines the reference answer and atomic facts for each question. The deterministic scorer aggregates supported facts by question and strategy. Fact coverage is the proportion of required facts supported by at least one reviewed top-10 chunk.

Citation accuracy is evaluated independently from semantic support. A passage can be irrelevant to a question while still having an accurate document/page citation.

## 3. Results

| Metric | Fixed 500-token chunks | Structure-aware chunks |
| --- | ---: | ---: |
| Complete support | 19 / 41 (46.3%) | 25 / 41 (61.0%) |
| Partial support | 5 / 41 (12.2%) | 5 / 41 (12.2%) |
| No required-fact support in top 10 | 17 / 41 (41.5%) | 11 / 41 (26.8%) |
| Mean required-fact coverage | 53.3% | 67.2% |

Across the 82 question-strategy pairs:

- Complete support: 44 (53.7%)
- Partial support: 10 (12.2%)
- No required-fact support in the top 10: 28 (34.1%)

Structure-aware retrieval achieved higher mean fact coverage and more complete-support outcomes in this evaluation set. These results are descriptive for this corpus, question set, and retrieval configuration; they are not a statistically generalisable claim.

A no-support outcome means that the retrieved top 10 did not support any required fact for that question. It does not prove that the source corpus contains no answer.

## 4. Citation and source verification

- 820 / 820 citation assessments were accurate (100%).
- All 820 review rows have `source_verified=yes`.
- All 54 original pages flagged for visual review were inspected in the committed contact sheets. This includes the PFRDA VCIP definition (q34) and the Special Bearer Bonds Ordinance passage (x04).
- The q04 structure rank-1 passage was corrected from a false positive: it was a heading-only passage and did not contain the operative beneficial-owner rules.

## 5. Material limitations

### Superseded RBI Digital Lending circular

The 2022 RBI Digital Lending circular used by q21–q24 and q31–q33 is marked repealed and replaced by the RBI (Digital Lending) Directions, 2025. Those question scores assess retrieval against the historical source specified in the current answer key. They must not be presented as evidence of current regulatory requirements.

### SEBI Research Analysts source reconciliation

For x03, the answer key was reconciled to the 2026 SEBI Research Analysts Master Circular (pp. 69–70). The current reference answer covers SCORES 2.0, the current platform URL, the two-level RAASB/SEBI review, and the physical-complaint route. The older SCORES URL and helpline are not treated as current facts.

### Historical Special Bearer Bonds Ordinance

The x04 source page is legible and its citation is visually verified. The source image bears a handwritten repeal note. This evaluation does not establish the Ordinance's current legal status.

### Evaluation boundary

Text alignment, source-page matching, and visual page inspection establish citation fidelity; they do not automatically establish semantic support. Semantic support is separately recorded through the evidence class and supported fact IDs. Results are retrieval-evidence metrics, not legal advice or a certification that every source instrument remains in force.

## 6. Reproducibility

Run from the repository root using the project's virtual environment:

```bash
./.venv/bin/python eval/answer_validation.py validate --answer-key eval/task3/answer_key.csv --reviews eval/task3/evidence_review.csv
./.venv/bin/python eval/answer_validation.py score --answer-key eval/task3/answer_key.csv --reviews eval/task3/evidence_review.csv --output eval/task3/answer_validation_scores.csv
```

Expected validation summary: 41 questions and 820 review rows, with no schema or supported-fact-ID errors.

## 7. Artifacts

- `answer_key.csv` — verified reference answers and required facts
- `evidence_review.csv` — all 820 human evidence assessments
- `answer_validation_scores.csv` — 82 question-strategy score rows
- `chunk_text.jsonl` — full retrieved chunk text
- `source_alignment_report.md` and `source_alignment_summary.json` — source-page alignment diagnostics
- `PROGRESS.md` — detailed execution status and remaining release checks

**Release gate:** local validation and scoring passed (41 questions; 820 evidence rows; 82 scores generated). GitHub Actions passed on commit `d562196`. Merge remains the final release action.
