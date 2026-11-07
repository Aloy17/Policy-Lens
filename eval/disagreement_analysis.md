# Phase 3 — selected retrieval disagreement analysis

Status: **retrieval evidence export prepared; passage-level interpretation pending**.

This review uses the Phase 3 disagreement summary supplied from the local evaluation run. The underlying `retrieval_log_phase3.csv` was not committed to the repository, so the retrieved passage previews cannot yet be independently inspected from this branch.

## Selected cases

| Question | Gold reference | Fixed-size result | Structure-aware result | Review purpose |
|---|---|---|---|---|
| q04 — Beneficial-owner identification | `rbi_kyc_2024`, PDF page 38 | No gold hit in top 10; top result is SEBI Master Circular for Depositories, pages 20–21 | Gold passage at rank 1, RBI KYC Direction page 38 | Clear structure-aware success; inspect whether each returned passage actually addresses beneficial-owner identification |
| q17 — FPI proof of address | `rbi_kyc_2024`, PDF pages 94–95 | First gold hit at rank 8; top result is SEBI Depositories, pages 11–12 | Gold passage at rank 1, RBI KYC Direction page 94 | Table-question case; inspect extracted table headers, row/category alignment, and whether the retrieved text preserves the relevant cell |
| q13 — KYC/AML-CFT staff training | `rbi_kyc_2024`, PDF page 70 | First gold hit at rank 5; top result is PFRDA KYC AML CFT, page 7 | No gold hit in top 10; same PFRDA document ranks first | Counterexample; compare the PFRDA passage with the RBI source passage and assess whether the query is sufficiently discriminative |

## Interpretation guardrails

- These are retrieval outcomes under the current corpus, question set, embedding model, and index settings—not universal claims about either chunking strategy.
- Rank differences alone do not establish why a strategy succeeded or failed.
- q17 is labelled as a table question, but that label does not prove table extraction caused the observed ranking.
- q13's shared top-ranked PFRDA document may indicate overlapping terminology, but this must be confirmed by reading both passages.
- Gold page references remain provisional until checked against the exact local PDF version and page-number convention.

## Next evidence step

Once `eval/retrieval_log_phase3.csv` is available locally, run:

```bash
PYTHONPATH=. python eval/inspect_disagreements.py
```

Review `eval/selected_disagreement_evidence.csv` alongside the source PDF pages. Record passage-level observations here, then update the gold-set review register if a cited page or label is incorrect. Do not describe a causal mechanism unless the retrieved chunk contents support it.
