# Phase 3 — selected retrieval disagreement analysis

Status: **latest ranked evidence reviewed; source-PDF visual verification remains incomplete**.

Evidence: `eval/selected_disagreement_evidence.csv`, generated from the revised 2026-11-07 benchmark. It contains the top 10 results for each strategy for q04, q17, and q13 (60 rows). Previews are truncated; conclusions below are limited to the visible ranked evidence and gold-page-hit flags.

## q04 — Beneficial-owner identification

Gold reference: `rbi_kyc_2024`, PDF page 38.

- **Fixed-size:** no gold-page hit in the top 10. Rank 1 is SEBI's Master Circular for Depositories, pages 20–21 (score 0.611). Rank 2 is RBI KYC pages 5–6 (0.4974), a preliminary definition passage rather than the gold page.
- **Structure-aware:** exact gold page 38 at rank 1 (score 0.7235), section metadata `Part IV - Identification of Beneficial Owner`. The preview starts with paragraph 34, which directly concerns identifying beneficial owners when opening an account for a legal person.

**Interpretation:** structure-aware retrieves the expected section first; fixed-size ranks related beneficial-owner material from another document first and does not retrieve the gold page in its top 10. This is an observed ranking difference, not proof of a causal chunk-boundary mechanism.

## q17 — FPI proof-of-address table requirement

Gold reference: `rbi_kyc_2024`, PDF pages 94–95. Table-labelled question.

- **Fixed-size:** first gold-page hit at rank 8 (pages 93–94; score 0.4879). Rank 1 is SEBI Depositories pages 11–12, a general proof-of-address passage in a different regulatory context.
- **Structure-aware:** gold page 94 at rank 1 (score 0.5804), section `Annex IV`; another gold hit at rank 3 is explicitly marked `[TABLE 1]` and its preview includes the FPI Category I/II/III column labels. A further gold hit at rank 8 includes the UBO proof-of-address row and category values.

**Interpretation:** structure-aware places the correct annex/table first, while fixed-size's first result is a semantically similar but contextually wrong proof-of-address passage. The previews support retrieval of the relevant table, but the exact cell-to-column association and answer still require visual verification against the source PDF.

## q13 — KYC/AML-CFT staff training

Gold reference: `rbi_kyc_2024`, PDF page 70.

- **Fixed-size:** first gold hit at rank 5 (RBI pages 69–71; score 0.4862). The preview explicitly says training should differ for frontline staff, compliance staff, and staff dealing with new customers.
- **Structure-aware:** no gold-page hit in the top 10. Rank 1 is PFRDA's KYC/AML/CFT master circular, page 7 (score 0.567); rank 2 is RBI KYC pages 17–18, which concern designated-director/principal-officer responsibilities rather than the target training passage.
- Both strategies rank the PFRDA circular first, but the previews do not establish why structure-aware misses the RBI training page.

**Interpretation:** this is a counterexample to the overall structure-aware lead: fixed-size retrieves the expected passage at rank 5; structure-aware misses it within top 10. The result demonstrates that the aggregate advantage is not uniform and cannot be explained from these previews alone.

## Summary

The selected cases show **two structure-aware wins (q04, q17) and one fixed-size win (q13)**. This is consistent with, but does not independently prove, the aggregate results:

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Recall@3 | 0.52 | 0.56 |
| Recall@5 | 0.56 | 0.68 |
| Recall@10 | 0.76 | 0.76 |
| MRR | 0.527762 | 0.558667 |

Structure-aware leads early retrieval and MRR overall and on the five table-labelled questions; fixed-size leads on the five paraphrased questions. Structure-aware indexes 14,157 chunks versus 5,973 for fixed-size (about 2.37x). Do not claim universal superiority or select a production strategy without reconciling storage and latency.

## Limitations and remaining validation

- The 25-question gold set is small, RBI-concentrated, and not a blind holdout.
- The 60 selected rows contain truncated previews, not full source passages.
- q17's exact table-cell alignment must be checked in the source PDF before asserting the Category III answer.
- q04 and q13 source-page alignment should be confirmed as part of the full gold-page audit.
- The 10-page parser sample found table/numeric/reading-order risks; visual review of S03/S05/S06/S07 is not complete. Do not represent these as visually verified.
- OCR accuracy was not measured: all 10 sampled pages were classified as native text and no OCR was run.
- No causal claims about chunking, parsing, or cleaning should be made from rank differences alone.
