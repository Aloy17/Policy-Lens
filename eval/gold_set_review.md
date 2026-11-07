# Gold-set review register

Status: **source audit in progress; q04, q13, q16–q20, and q25 have focused source evidence; q21–q24 still require an accessible copy of the historical Digital Lending PDF and local page checks remain outstanding.**

The canonical questions are in `questions.csv`. The evaluator's page fields use **1-based PDF page indices**, not the printed page numbers visible in the RBI document. In the RBI KYC PDF checked here, the printed page number is one less than the PDF page index for the reviewed passages (for example, PDF page 38 carries printed page 37). Keep this distinction explicit in all evidence notes.

## Review summary

| Review item | Current state | Required action |
|---|---|---|
| Question count | 25 records | Confirm unchanged after review |
| Table questions | 5 labels (q16–q20) | Verify all five depend on table cells/values |
| Paraphrased questions | 5 labels (q02, q08, q14, q21, q23) | Count preserved; q15 remains non-paraphrased |
| Gold document IDs | Three RBI documents | Confirm exact document version and title |
| Gold page ranges | q04, q13, q16–q20, q25 source-checked from official source evidence | Verify remaining KYC and Digital Lending page references against the exact corpus PDFs |
| Page convention | 1-based PDF page indices | Confirmed for reviewed KYC pages; printed page = PDF page minus one in these locations |

## Per-question evidence log

| ID | PDF page verified? | Printed page / section | Evidence description | Label accepted? | Reviewer note |
|---|---|---|---|---|---|
| q04 | Yes | PDF 38 / printed 37 / Part IV - Identification of Beneficial Owner | Paragraph 34 addresses identifying and taking reasonable steps to verify beneficial owners when opening an account for a legal person. | Yes, provisional | Exact passage begins on PDF page 38. The table of contents lists the section at printed page 38, but the section heading itself appears on printed page 37; evaluation metadata is PDF-index based. |
| q13 | Yes | PDF 70 / printed 69 / Paragraph 70, Hiring of Employees and Employee training | Paragraph 70 requires screening, appropriate staff attributes, ongoing KYC/AML/CFT training, differentiated training focus for frontline/compliance/new-customer staff, and trained audit staff. | Yes, provisional | The training paragraph continues across the printed-page boundary; PDF page 70 is the correct evaluator page for the retrieved passage. |
| q15 | Yes, source text | PDF 58–59 / printed 57–58 / Paragraph 56(j), CKYCR retrieval | An RE should retrieve KYC records through the customer's KYC Identifier and should not require resubmission of the same records or additional identification details unless one of the specified exceptions applies: changed customer information, incomplete/outdated or non-compliant records, expired document validity, or a need for identity/address verification, enhanced due diligence, or risk profiling. | Yes, provisional | Replaces a near-duplicate of q06. Local PDF page alignment must still be confirmed against the exact corpus file. |
| q16 | Yes | PDF 94 / Annex IV, Entity Level | Constitutive documents (including memorandum and articles of association and certificate of incorporation) are marked Mandatory for Categories I, II, and III. | Yes, provisional | The question specifically asks about Category I; the row confirms Mandatory. |\n| q17 | Yes | PDF 94 / Annex IV, Entity Level | Entity-level proof of address is Mandatory for Category III, with the explicit qualification “other than Power of Attorney”. | Yes, provisional | Answer is yes, but retain the PoA exclusion. |\n| q18 | Yes | PDF 95 / Annex IV, Senior Management | Photographs are marked Exempted for all three FPI categories; the asterisk note says starred documents are not required while opening the bank account, though they may be supplied on demand. | Yes, provisional | Preserve the footnote; do not imply the documents can never be requested. |\n| q19 | Yes | PDF 95 / Annex IV, Ultimate Beneficial Owner | UBO proof of identity is Exempted for Categories I and II and Mandatory for Category III. | Yes, provisional | Question now explicitly identifies the UBO row to avoid ambiguity with entity-level or senior-management proof of identity. |\n| q20 | Yes | PDF 95 / Annex IV, Authorized Signatories | The authorized-signatories list and signatures are Mandatory for Category III. Categories I and II permit the Global Custodian signatory list when there is a PoA to the Global Custodian. | Yes, provisional | Question now names Category III and the exact row; the Category I/II caveat belongs in the answer. |

| q25 | Yes | PDF 1 / revised filing requirements, commercial-bank row | The first page states that all audited returns for commercial banks are due within five working days from signing of the Auditor’s report. | Yes, narrowed | The original question was overbroad. It is now explicitly scoped to commercial banks and “all audited returns”. The separate NBFC filing table has different periodicity-based timelines; do not conflate them. |\n\nQuestions q01–q03, q05–q12, and q14 still require individual verification against the exact corpus PDFs. The official RBI notification page and an accessible copy of the original circular provide source text for q21–q24; however, the local corpus PDF page alignment still needs confirmation before the gold page ranges are accepted. Do not treat this register as a completed gold-set audit.

## Source-version caveats

- The RBI KYC PDF in the corpus is the Master Direction dated February 25, 2016, **updated as on August 14, 2025**. The manifest now records `issue_date=2016-02-25` and `updated_as_of=2025-08-14`. The historical `doc_id` remains `rbi_kyc_2024` to preserve compatibility with existing indexed metadata; it is a legacy identifier, not the document issue year. The RBI subsequently repealed the 2016 Master Direction with immediate effect on November 28, 2025 for Payment System Providers and Payment System Participants, and issued entity-specific 2025 KYC Directions. Treat this corpus PDF as a historical consolidated snapshot, not a current universal KYC rulebook.
- The Digital Lending Guidelines dated September 2, 2022 are retained as a historical source for this test set. RBI issued the consolidated Digital Lending Directions, 2025 on May 8, 2025; do not present the 2022 document as current policy.
- A retrieval hit is judged against the selected gold document/page only; an equivalent answer in a later or superseding circular is not counted unless explicitly added to the gold set.


## CKYCR source check (q15)

The August 14, 2025 consolidated RBI KYC Master Direction states in paragraph 56(j) that an RE should obtain the customer's KYC Identifier and retrieve KYC records from CKYCR rather than require the customer to resubmit the same records or additional identification details, subject to the four stated exceptions. The passage begins on printed page 57 and continues onto printed page 58. The question now targets this distinct rule instead of duplicating q06's secrecy obligation. The proposed evaluator range is PDF pages 58–59 based on the document's printed-page offset; verify this against the exact local corpus PDF before final acceptance.

## Digital Lending source check (q21–q24)

The official RBI notification page for the September 2, 2022 circular is accessible and explicitly states that the circular has since been repealed and points readers to the Digital Lending Directions, 2025. The source text confirms:

- **q21:** Outsourcing to an LSP/DLA does not diminish the RE's obligations; the RE remains responsible for ensuring compliance by its LSPs and DLAs.
- **q22:** Existing digital loans sanctioned on or before the circular date were to comply by **November 30, 2022**.
- **q23:** Fees/charges payable to an LSP in the credit-intermediation process are paid directly by the RE, not the borrower.
- **q24:** The KFS must be provided before contract execution and include APR, recovery mechanism, the designated grievance-redressal officer, and the cooling-off/look-up period. Fees/charges not included in the KFS cannot be charged to the borrower.

Source: RBI notification RBI/2022-23/111 dated September 2, 2022. The page and accessible PDF establish substantive answers, but confirm the exact local PDF page ranges before accepting the labels as final. The historical circular must not be represented as current policy.
