# Gold-set review register

Status: **partially source-verified; remaining 22 question references and category labels pending review**.

The canonical questions are in `questions.csv`. The evaluator's page fields use **1-based PDF page indices**, not the printed page numbers visible in the RBI document. In the RBI KYC PDF checked here, the printed page number is one less than the PDF page index for the reviewed passages (for example, PDF page 38 carries printed page 37). Keep this distinction explicit in all evidence notes.

## Review summary

| Review item | Current state | Required action |
|---|---|---|
| Question count | 25 records | Confirm unchanged after review |
| Table questions | 5 labels (q16–q20) | Verify all five depend on table cells/values |
| Paraphrased questions | 5 labels (q02, q08, q14, q21, q23) | Compare source wording and query wording; revise weak labels |
| Gold document IDs | Three RBI documents | Confirm exact document version and title |
| Gold page ranges | q04, q13, q17 source-checked | Verify q01–q03, q05–q12, q14–q16, q18–q25 |
| Page convention | 1-based PDF page indices | Confirmed for reviewed KYC pages; printed page = PDF page minus one in these locations |

## Per-question evidence log

| ID | PDF page verified? | Printed page / section | Evidence description | Label accepted? | Reviewer note |
|---|---|---|---|---|---|
| q04 | Yes | PDF 38 / printed 37 / Part IV - Identification of Beneficial Owner | Paragraph 34 addresses identifying and taking reasonable steps to verify beneficial owners when opening an account for a legal person. | Yes, provisional | Exact passage begins on PDF page 38. The table of contents lists the section at printed page 38, but the section heading itself appears on printed page 37; evaluation metadata is PDF-index based. |
| q13 | Yes | PDF 70 / printed 69 / Paragraph 70, Hiring of Employees and Employee training | Paragraph 70 requires screening, appropriate staff attributes, ongoing KYC/AML/CFT training, differentiated training focus for frontline/compliance/new-customer staff, and trained audit staff. | Yes, provisional | The training paragraph continues across the printed-page boundary; PDF page 70 is the correct evaluator page for the retrieved passage. |
| q17 | Yes | PDF 94–95 / printed 93–94 / Annex IV | Annex IV table states entity-level proof of address is mandatory for Category III, with the qualification that proof by Power of Attorney is not accepted for Category III. | Yes, provisional | Answer to the yes/no question is **yes**. The Category III cell says “Mandatory other than Power of Attorney”; avoid flattening this qualification. |

All other questions q01–q03, q05–q12, q14–q16, and q18–q25 remain pending individual verification. Do not treat this table as a completed gold-set audit.

## Source-version caveats

- The RBI KYC PDF in the corpus is the Master Direction dated February 25, 2016, **updated as on August 14, 2025**. The manifest currently labels it `issue_date=2024-01-01`; that is incorrect as an original issue date and must be corrected or replaced with explicit `issue_date=2016-02-25` and `updated_as_of=2025-08-14` metadata. The RBI subsequently repealed the 2016 Master Direction with immediate effect on November 28, 2025 for Payment System Providers and Payment System Participants, and issued entity-specific 2025 KYC Directions. Treat this corpus PDF as a historical consolidated snapshot, not a current universal KYC rulebook.
- The Digital Lending Guidelines dated September 2, 2022 are retained as a historical source for this test set. RBI issued the consolidated Digital Lending Directions, 2025 on May 8, 2025; do not present the 2022 document as current policy.
- A retrieval hit is judged against the selected gold document/page only; an equivalent answer in a later or superseding circular is not counted unless explicitly added to the gold set.
