# Gold-set history and evaluation-independence disclosure

## Why this record exists

The Case Study 2 preparation checklist says that evaluation questions and gold pages should be written before tuning the pipeline, to reduce evaluation bias. The deliverables also call for a 25-question evaluation set with gold document/page references. This record preserves the earliest committed question set and explains later corrections so that the submission does not present a revised set as an untouched holdout.

## What the repository history establishes

- The earliest recoverable `eval/questions.csv` was committed in the repository's initial commit, `f626b1ae7f28ca299921d41177e807755aec086a`, at **2026-11-07 08:21:04 UTC**.
- That snapshot contains 25 questions (q01–q25), five table-question labels (q16–q20), and 2 rows marked as paraphrased.
- The exact original snapshot is preserved at [questions_pre_revision_2026-11-07.csv](questions_pre_revision_2026-11-07.csv). It is an archival copy, not the current canonical gold set.
- The benchmark record documents an earlier 25-question baseline before the subsequent gold-set edits: fixed-size Recall@3/5/10 = 0.40/0.44/0.64 and MRR = 0.414825; structure-aware = 0.64/0.72/0.80 and MRR = 0.590667.
- The later corrected 25-question rerun reports fixed-size Recall@3/5/10 = 0.52/0.56/0.76 and MRR = 0.527762; structure-aware = 0.60/0.72/0.80 and MRR = 0.578667. These are results for the corrected question/gold-page version, not a strictly unchanged paired comparison with the earlier baseline.

## Revisions made after the earlier baseline

The repository history records, among other gold-set corrections:

| Questions | Change | Why it matters |
|---|---|---|
| q02 | Reworded to ask about circumstances triggering customer identification; narrowed the gold target to PDF page 22. | Changes question wording and target scope. |
| q03 | Reworded to ask about conditions for relying on third-party customer due diligence; gold range set to PDF pages 22–23. | Separates this obligation from q02 rather than treating both as the same customer-identification question. |
| q13 | Gold range corrected/expanded to PDF pages 69–70. | Corrects the source-page coverage for the staff-training passage. |
| q14 | Gold page corrected to PDF page 46 and the question focused on PEP controls. | Changes the target from the earlier high-risk-jurisdiction question/page. |

Relevant question-file commits include `e0343cd2f52035794ed7fba499ae4f2713500c7b` (q02/q03 separation), `d213edb984c193faba0fc35d4051816165f65349` (q14 page correction), and `5449827335754c8fbf8d7e631895872a7e6f9b28` (q13 range expansion). The source-review history also records the intermediate q13/q14 audit corrections.

These revisions improve semantic distinction and gold-page accuracy. However, because they followed an earlier benchmark, the corrected 25-question results must be described as a **post-audit corrected rerun**, not as results from an untouched blind holdout.

## How to interpret the November 14 evaluation

The November 14 evaluation expanded the dataset to 42 records, of which 41 were usable after validation. It is a larger supplementary evaluation. It must not be described as the assignment's original 25-question set, and it does not erase the chronology of the earlier gold-set revisions.

## What can and cannot be claimed

- **Can be claimed:** a 25-question set was committed before the first recorded benchmark; the original file is preserved; later gold-set revisions and corrected rerun results are documented.
- **Can be claimed:** the current canonical 25-question set has 25 records, five table questions, and five paraphrased questions, as checked in the gold-set review.
- **Cannot be claimed:** that the corrected 25-question set was an untouched holdout throughout all benchmarking.
- **Cannot be proven from the available Git history alone:** that the earliest committed question set predates every retrieval/chunking tuning decision. The commit proves when the file first appears in this repository, not the full chronology of work performed before that commit.

## Reporting treatment

Use the original 25-question baseline and the corrected 25-question rerun as two separately labelled historical results. Explain the q02/q03/q13/q14 changes and do not attribute differences between those runs solely to retrieval-code changes. Present the November 14 41-question evaluation as supplementary expanded evidence. Retain the non-blind / post-audit limitation in the final report.

