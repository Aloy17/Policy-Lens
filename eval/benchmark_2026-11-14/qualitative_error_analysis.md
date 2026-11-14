# Qualitative retrieval inspection — 2026-11-14

## Scope and evidence boundary

This inspection uses the selected Chroma chunk records pasted from the local database after the retrieval benchmark. The records include chunk IDs, document IDs, page ranges, section titles, and extracted text.

The pasted output does **not** include the benchmark question ID, retrieval rank, or strategy-to-question association for each record. Therefore:
- The content of each supplied chunk can be assessed directly.
- Previously recorded case-to-strategy/rank observations are retained as benchmark observations, not independently reconstructed from this paste.
- This is retrieved-chunk text inspection, not visual/source-PDF verification. The original PDF page images were not supplied for this review.

## Case findings

| Question | Retrieved chunk evidence supplied | Content assessment | Finding |
|---|---|---|---|
| q03 — Third-party CDD conditions | Fixed chunk rbi_kyc_2024_fixed_e525b18753fd_29, pp. 22–24 | Contains the operative third-party CDD reliance conditions: obtain CDD records immediately; make identification copies/documentation available without delay; third party must be regulated/supervised/monitored and have CDD/record-keeping controls; it must not be based in a high-risk jurisdiction; ultimate responsibility remains with the RE. | **Substantive evidence present in fixed-size chunk.** This is a strong content match, not merely a page hit. The previously noted structure-aware top-three results were unrelated; one supplied structure chunk concerns ESG-rating-provider outsourcing, not RBI customer due diligence. |
| q04 — Beneficial-owner identification | Structure chunk rbi_kyc_2024_structure_e525b18753fd_59, p. 38 | Contains only the heading “Part IV - Identification of Beneficial Owner”. It does not contain the operative identification test or definition for a legal person. | **Heading-only / insufficient evidence.** The page-overlap hit must not be counted as a substantive retrieval success. The earlier observation that fixed-size missed the expected passage remains; neither supplied chunk establishes the answer. |
| q07 — CKYCR upload deadline | Structure chunk rbi_kyc_2024_structure_e525b18753fd_82, pp. 57–58 | Explicitly states that REs shall capture KYC records and upload them to CKYCR within 10 days of commencement of the account-based relationship. | **Substantive evidence present in structure-aware chunk.** The supplied excerpt does not include the corresponding fixed-size chunk, so this paste alone cannot verify fixed-size content. |
| q08 — Action after CKYCR update | Structure chunk rbi_kyc_2024_structure_e525b18753fd_84, pp. 58–59 | Explicitly states that after CKYCR informs an RE of an update to an existing customer's KYC record, the RE shall retrieve the updated record from CKYCR and update its own KYC record. | **Substantive evidence present in structure-aware chunk.** The supplied excerpt does not include the corresponding fixed-size chunk, so this paste alone cannot verify fixed-size content. |
| q09 — Cross-border wire-transfer information | Fixed chunk rbi_kyc_2024_fixed_e525b18753fd_76, pp. 66–68; structure chunk rbi_kyc_2024_structure_e525b18753fd_92, pp. 65–66 | Fixed text refers to complete originator and beneficiary information being preserved and to the flow of complete wire-transfer information. Structure text refers to required and accurate originator information, required beneficiary information, and responsibilities of ordering/intermediary/beneficiary REs. Neither supplied excerpt enumerates the complete required data elements. | **Relevant but partial evidence in both.** These chunks are on-topic and support the general obligation, but the excerpts alone do not establish a complete answer to “what information” is required. Do not treat them as fully answer-sufficient. |
| q16 — Category I FPI constitutive documents | Fixed chunk rbi_kyc_2024_fixed_e525b18753fd_109, pp. 93–94 | Includes the Annex IV table with the constitutive-documents row and Category I column; the cell is explicitly “mandatory”. | **Substantive table evidence present in fixed-size chunk.** This verifies the answer, not just the page overlap. The supplied paste does not include a corresponding structure-aware table chunk. |
| x03 — Research-analyst complaint escalation | Fixed chunk sebi_master_circular_for_research_analysts_fixed_905187ba5567_24, pp. 31–33; structure chunk sebi_master_circular_for_research_analysts_structure_905187ba5567_9, p. 3 | The fixed chunk states that if the investor's complaint is not redressed satisfactorily by the research analyst, the investor may lodge a complaint with SEBI on its SCORES portal. This supports the requested destination, although it is from the investor-charter section (pp. 31–32), not the gold page 10. The structure chunk contains only the heading “Investor Complaints”. | **Fixed-size contains answer-supporting evidence outside the gold page; structure-aware heading is insufficient.** The fixed chunk is a content-level success for the asked destination despite the page mismatch. The expected page-10 passage was not present in the supplied chunks. |

## Overall interpretation

1. Page overlap is not sufficient evidence of retrieval quality. q04 demonstrates a false-positive page hit: the retrieved chunk is only a section heading.
2. q03 and q16 provide clear examples of fixed-size chunks containing substantive answer evidence.
3. q07 and q08 provide clear examples of structure-aware chunks containing substantive answer evidence.
4. q09 is a partial match in both strategies: the chunks establish the relevant wire-transfer obligations and roles but do not expose all required information elements in the supplied excerpts.
5. x03 illustrates why gold-page matching can undercount answer-supporting retrieval: the fixed chunk contains the requested SCORES escalation route on a different page, while the structure chunk is only a heading.

## Remaining verification limits

- The pasted output omits question IDs and retrieval ranks, so it cannot independently reconstruct the full top-k ordering or prove which selected chunk appeared for which query/rank. Case associations and rank descriptions rely on the benchmark inspection notes already recorded.
- Only selected chunks were supplied, not every top-k result for both strategies.
- Original source-PDF page images were not included. This review checks the extracted Chroma chunk text against the gold question/passage definitions; it does not certify OCR/layout fidelity against page images.
- q07/q08 counterparts and q16 structure-aware counterpart are not included in the pasted extract, so no direct cross-strategy content comparison is possible for those cases.

## Recommendation

Treat the qualitative review as **partially completed, with content-level evidence checked for the supplied chunks**. Do not claim full source-PDF verification or complete top-k case reconstruction. Retain both chunking strategies as viable; use these cases to improve the evaluator so answer-supporting evidence can be distinguished from heading-only and partial matches.
