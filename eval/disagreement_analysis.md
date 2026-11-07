# Phase 3 — selected retrieval disagreement analysis

Status: **ranked passage previews inspected; source-page and gold-label verification still pending**.

Evidence source: the committed `selected_disagreement_evidence.csv`, generated from the user's successful Phase 3 run. It contains the top 10 results for each strategy for q04, q17, and q13 (60 rows total). Each preview is truncated to 200 characters; this supports a preliminary passage-level interpretation, not a full source audit.

## q04 — Beneficial-owner identification

Gold reference: `rbi_kyc_2024`, PDF page 38.

- **Fixed-size:** no gold-page hit in the top 10. Rank 1 is SEBI's Master Circular for Depositories, pages 20–21 (score 0.611). Rank 2 is the RBI KYC document, pages 5–6 (score 0.4974); its preview discusses the ownership/entitlement threshold for a partnership, but it does not match the selected page-38 gold reference.
- **Structure-aware:** rank 1 is the expected RBI KYC document, page 38 (score 0.7235), with section metadata `Part IV - Identification of Beneficial Owner`. Its preview begins with paragraph 34, explicitly addressing identification of beneficial owners when opening an account for a legal person.

**Evidence-based interpretation:** structure-aware retrieval surfaces the exact expected section as its first result. Fixed-size retrieval is distracted by semantically related beneficial-owner passages in other documents and by an earlier RBI definition passage. This is a ranking observation; it does not by itself prove that chunk boundaries caused the improvement.

## q17 — FPI proof-of-address table requirement

Gold reference: `rbi_kyc_2024`, PDF pages 94–95. This is one of the five table-labelled questions.

- **Fixed-size:** first gold-page hit at rank 8 (pages 93–94; score 0.4879). Its top result is SEBI Depositories, pages 11–12, whose preview lists general proof-of-address documents rather than the FPI category table.
- **Structure-aware:** rank 1 is the expected RBI KYC document, page 94 (score 0.5804), section `Annex IV`. Its preview preserves the table title and column headers for FPI type and Categories I, II, and III. A second gold result at rank 3 (pages 94–95) is explicitly marked `[TABLE 1]` and its preview includes the category columns. Rank 8 also retrieves page 95 with the UBO proof-of-address row and category-specific values.

**Evidence-based interpretation:** structure-aware results bring the relevant FPI annex/table to the top and retain visible table structure in the preview. The fixed-size top result matches the phrase “proof of address” but belongs to a different regulatory context. This supports a table-retrieval observation, although full-cell verification against the source PDF is still required before stating the Category III answer.

## q13 — KYC/AML-CFT staff training

Gold reference: `rbi_kyc_2024`, PDF page 70.

- **Fixed-size:** first gold hit at rank 5 (RBI pages 69–71; score 0.4862). Its preview explicitly mentions that training should differ for frontline staff, compliance staff, and staff dealing with new customers.
- **Structure-aware:** no gold-page hit in the top 10. Its rank 1 result is PFRDA's KYC/AML/CFT master circular, page 7 (score 0.567); the preview discusses the KYC/AML/CFT policy and reporting entities. Its rank 2 is the RBI KYC document, pages 17–18, concerning designated-director/principal-officer responsibilities rather than the training passage.
- Both strategies rank the PFRDA document first, but the previews do not establish that this is the reason structure-aware missed the RBI training passage.

**Evidence-based interpretation:** this is a counterexample to the overall structure-aware advantage: fixed-size retrieves the expected training passage within the top five, while structure-aware does not retrieve it within the top ten. The shared PFRDA top result suggests broad KYC/AML/CFT terminology overlap, but the available previews are insufficient to attribute the miss to a specific chunking or parsing defect.

## Summary for the report

These three cases provide two structure-aware wins (q04 and q17) and one fixed-size win (q13). The outcomes align with the overall measured Recall@10 and MRR advantage for structure-aware chunking in this 25-question set, while q13 demonstrates that the result is not uniform.

Do not claim universal superiority. The evaluation is limited to this question set and current corpus/index configuration. The CSV previews are only 200 characters; full chunk contents and source PDF pages must be checked before finalizing causal explanations or the exact FPI table answer.

## Remaining checks

1. Verify the exact PDF pages and printed-page convention for q04, q17, and q13; then verify all other gold references.
2. For q17, inspect the complete table rows and column alignment in the source PDF before accepting the answer label.
3. For q13, compare the complete RBI training passage with the PFRDA rank-1 passage; retain the failure as a counterexample unless stronger evidence explains it.
4. Complete the ten-page parsing/OCR inspection and before/after cleaning evidence.
