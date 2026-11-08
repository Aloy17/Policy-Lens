# Sampled-page inspection findings

## Scope and limitations

- Random sample: 10 pages from a 5,050-page PDF frame (seed 2026).
- All 10 pages were classified as `text_native`; none met the OCR-candidate heuristic, so OCR was not executed.
- These observations describe this sample only. They do not establish corpus-wide OCR accuracy or scan prevalence.
- The cleaning preview was run on the sampled subset. Repeated-header detection can differ from full-document ingestion cleaning.
- Findings below are based on the exported native text, table output, and cleaning previews. Visual confirmation against the rendered source pages remains necessary for ambiguous table geometry and reading order.

## Page-level findings

| Sample | Document / PDF page | Assessment | Evidence and implications |
|---|---|---|---|
| S01 | DPDP Rules 2025 / 27 | Good native extraction | Hindi gazette header and English provisions are retained. Cleaning mainly normalizes whitespace and indentation. |
| S02 | SEBI Depositories / 35 | Good native extraction | Numbered clauses, subclauses, and footnote references remain readable. |
| S03 | SEBI Depositories / 170 | Table numeric distortion | Native extraction and cleaned text preserve the medium-risk multiplier as `1.5`. Reconstructed table output renders it as `15 .`. This is a table-reconstruction fidelity defect, not a whitespace-cleaning defect. Verify numeric table cells against the source PDF. |
| S04 | SEBI InvITs / 19 | Good native extraction | Clause numbering, prose, and footnote references are retained. |
| S05 | SEBI LODR 2026 / 82 | Poor wide-table reconstruction | The multi-level, wide table has fragmented headers and column labels. Relationships between columns are difficult to recover from the serialized table. |
| S06 | SEBI LODR 2026 / 213 | Table-cell content loss | Native extraction and reconstructed table output preserve “Principle 6, Question 7 of Essential Indicators”. The cleaned-text section omits the cross-reference field entirely. This indicates a table-cell content preservation issue; it does not establish that the numeral alone was dropped. |
| S07 | SEBI Merchant Bankers / 104 | Potential reading-order / table association risk | Native extraction contains wrapped circular numbers, dates, and subjects. The text representation makes row associations difficult to assess, but does not independently prove that reconstructed rows are incorrectly associated. Treat this table as requiring source verification. |
| S08 | SEBI Mutual Funds / 217 | Good table reconstruction | The three InvIT investment limits (10% of issuer units, 10% of scheme NAV, and 5% of scheme NAV) and the remarks are represented coherently. |
| S09 | SEBI Stock Brokers / 246 | Good native extraction | Numbered password-security and session-management provisions remain readable. |
| S10 | SEBI Stock Brokers / 322 | Good native extraction | Cloud-control requirements and subclauses remain readable. |

## Aggregate assessment

- Native text was available on all 10 sampled pages.
- OCR was not run on any sampled page; OCR word accuracy is therefore **not measured** by this sample.
- Cleaning generally improves whitespace and indentation without obvious broad content loss in the prose samples.
- The principal observed risks are table structure, numeric fidelity in table cells, and multi-column reading order.
- Four pages (S03, S05, S06, S07) warrant explicit table/layout caution: numeric reconstruction fidelity (S03), wide-table structure (S05), table-cell content preservation (S06), and potential row-association ambiguity (S07).

## Recommended treatment

1. Preserve source-page provenance and page-level references for every retrieved passage.
2. Treat reconstructed tables as candidate evidence, not authoritative values, when headers are multi-level, columns are wide, or cell values are numeric.
3. For high-impact numeric or regulatory answers, verify the value against the original PDF page or a separately validated table representation.
4. Keep the native extracted text alongside table serialization so that retrieval and answer validation can fall back to the original reading-order text.
5. Report OCR accuracy as **not evaluated** for this sample. A separate representative scan sample with manually transcribed ground truth is required to calculate OCR word accuracy.
6. Visual verification of S03, S05, S06, and S07 against rendered PDF pages was not completed in this review. Treat the table/layout observations as extraction-output findings and unresolved visual-validation items, not visually confirmed defects.

## Interpretation

This sample supports the conclusion that native-text extraction and prose cleaning are functioning well on the sampled pages, but it also exposes meaningful layout-sensitive failure modes. It does not justify a claim that all corpus tables are reliable, nor does it provide an OCR accuracy estimate.

## Source-linked PDF cleaning example

- **Source document:** `sebi_master_circular_for_depositories`
- **Source file:** `data/pdfs/sebi_master_circular_for_depositories.pdf`
- **PDF page:** 170
- **Sample:** S03

The native text extraction contains excessive whitespace and indentation:

    High risk                         3
              Medium High risk                2
              Medium risk                         1.5
              Low risk                         1

The cleaned text normalizes whitespace while preserving the labels and values:

    High risk 3
    Medium High risk 2
    Medium risk 1.5
    Low risk 1

**Observed cleaning effect:** Excessive spacing and indentation are removed. The four risk labels and corresponding values remain present in the cleaned text.

**Important distinction:** The separately reconstructed table output represents the medium-risk value as `15 .` instead of `1.5`. This is a table-reconstruction fidelity issue, not evidence that the whitespace-cleaning operation changed the value.

**Validation requirement:** Numeric table values must be checked against the original PDF page before being used as authoritative evidence.
