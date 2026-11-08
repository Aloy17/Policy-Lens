# Gold-set review register

Status: **source audit in progress; q01–q20 and q25 have source-level checks of varying depth. q21–q24 have official source-text checks. Exact local corpus PDF page alignment and manual visual checks remain outstanding.**

The canonical questions are in `questions.csv`. The evaluator's page fields use **1-based PDF page indices**, not the printed page numbers visible in the RBI document. In the RBI KYC PDF checked here, the printed page number is one less than the PDF page index for the reviewed passages (for example, PDF page 38 carries printed page 37). Keep this distinction explicit in all evidence notes.

## Review summary

| Review item | Current state | Required action |
|---|---|---|
| Question count | 25 records | Confirm unchanged after review |
| Table questions | 5 labels (q16–q20) | Verify all five depend on table cells/values |
| Paraphrased questions | 5 labels (q02, q08, q14, q21, q23) | Count preserved; q15 remains non-paraphrased |
| Gold document IDs | Three RBI documents | Confirm exact document version and title |
| Gold page ranges | q01, q04, q13–q20, q25 have focused source evidence | Verify remaining KYC and Digital Lending page references against the exact corpus PDFs |
| Page convention | 1-based PDF page indices | Confirmed for reviewed KYC pages; printed page = PDF page minus one in these locations |

## Structured 25-question audit — 2026-11-07

This pass checked the canonical CSV against the manifest and the existing source-review evidence in this register. It verifies record structure, document identity, page-range bounds, question intent, and category semantics. It does **not** replace a page-by-page inspection of the exact 37 local corpus PDFs. Therefore the final local page-alignment status remains open for every question, even where official-source page mapping is already documented.

### Structural and manifest checks

- Exactly 25 unique, sequential IDs are present (q01–q25).
- All three expected document IDs exist in data/manifest.csv.
- Every inclusive page range is positive, ordered, and within the manifest page count: KYC 107 pages, Digital Lending 12 pages, and NBFC filing 3 pages.
- Category totals are exactly five table questions (q16–q20) and five paraphrased questions (q02, q08, q14, q21, q23).
- No question references a document outside the three intended RBI sources.
- These checks establish metadata consistency only; they do not establish that a passage is present on its labelled local PDF page.

### Question-by-question audit disposition

| ID | Gold reference | Semantic / label review | Disposition before local PDF check |
|---|---|---|---|
| q01 | KYC PDF p19 | Existing KYC customer opening another service; distinct from third-party CDD and CKYCR retrieval. | Content scope accepted; page provisional |
| q02 | KYC PDF p22 | Customer-identification triggers in paragraph 13; paraphrased label is reasonable. | Content and label accepted; page provisional |
| q03 | KYC PDF pp22–23 | Conditions for reliance on third-party CDD in paragraph 14; distinct from q02's identification triggers. | Content scope accepted; page split provisional |
| q04 | KYC PDF p38 | Beneficial-owner identification, paragraph 34; focused source check documented above. | Source-level accepted; page alignment locally provisional |
| q05 | KYC PDF pp45–46 | Enhanced due diligence for non-face-to-face onboarding; verify that the complete answer-bearing passage is covered by both pages. | Content scope accepted; page range provisional |
| q06 | KYC PDF p57 | Customer-information confidentiality; distinct from q15's CKYCR resubmission rule. | Content scope accepted; page provisional |
| q07 | KYC PDF p58 | Initial CKYCR upload deadline; distinct operation from q08 and q15. | Content scope accepted; page provisional |
| q08 | KYC PDF p59 | Retrieval and update after CKYCR notification; paraphrased label is reasonable. | Content and label accepted; page provisional |
| q09 | KYC PDF pp64–67 | Cross-border wire-transfer originator/beneficiary information; broad multi-paragraph scope makes both endpoints important. | Content scope accepted; exact local range provisional |
| q10 | KYC PDF p68 | PAN/Form 60 requirement for applicable transactions. | Content scope accepted; page provisional |
| q11 | KYC PDF p71 | Digital-KYC application authentication and access controls. | Distinct from q12; page provisional |
| q12 | KYC PDF p72 | Customer OTP validation/signature role; distinct from q11's official access controls. | Content scope accepted; page provisional |
| q13 | KYC PDF pp69–70 | Staff screening and KYC/AML-CFT training, paragraph 70; source-level check documented above. | Source-level accepted; page alignment locally provisional |
| q14 | KYC PDF p46 | PEP-specific identification, source-of-funds/wealth, senior approval, and monitoring; paraphrased label is reasonable. | Content and label accepted; page provisional |
| q15 | KYC PDF pp58–59 | CKYCR retrieval and exceptions to requesting resubmission; distinct from q06–q08. | Content scope accepted; page range provisional |
| q16 | KYC PDF p94 | Constitutive-documents row asks for a table value (Category I: Mandatory). | Table label justified; page/cell alignment provisional |
| q17 | KYC PDF pp94–95 | Proof-of-address table value for Category III; retain the Power of Attorney qualification. | Table label justified; exact cell alignment and page range provisional |
| q18 | KYC PDF p95 | Photograph exemption across FPI categories requires reading a table row and its footnote. | Table label justified; footnote/page alignment provisional |
| q19 | KYC PDF p95 | UBO proof-of-identity value for Category III requires the UBO table row. | Table label justified; page/cell alignment provisional |
| q20 | KYC PDF p95 | Authorized-signatory list/signature requirement for Category III requires the table row and category-specific qualification. | Table label justified; page/cell alignment provisional |
| q21 | Digital Lending PDF pp1–4 | RE responsibility when using an LSP/DLA; paraphrased label is reasonable. | Content and label accepted; local page range provisional |
| q22 | Digital Lending PDF p2 | Compliance deadline for existing digital loans; verify exact wording and date against local PDF. | Content scope accepted; page provisional |
| q23 | Digital Lending PDF pp4–5 | Allocation of LSP fees/charges to the RE rather than borrower; paraphrased label is reasonable. | Content and label accepted; page range provisional |
| q24 | Digital Lending PDF p5 | KFS disclosure contents; verify the answer-bearing Annex I passage is on the recorded local page. | Content scope accepted; page provisional |
| q25 | NBFC filing PDF p1 | Commercial-bank row; five-working-day deadline from auditor-report signature. The question is deliberately narrowed to avoid conflating NBFC timelines. | Source-level accepted; page provisional |

### Category quality assessment

**Table questions (q16–q20):** all five require reading a specific row/column intersection or its associated footnote in Annex IV. The category label is justified. q17, q18, and q20 are especially sensitive to row/column association and footnote handling; do not treat extracted linear text alone as proof of correct cell mapping.

**Paraphrased questions (q02, q08, q14, q21, q23):** all five ask for the same underlying rule using question wording rather than copying a distinctive source sentence. They are materially rephrased at the question level. q02 and q08 are close to the source's legal concepts but do not reproduce the source clause wording. The labels are accepted.

### Additional source-page inspection — 2026-11-07

The manifest's published RBI source URLs were opened and their answer-bearing passages inspected. This strengthens the content-level checks but must not be represented as a byte-for-byte inspection of the user's packaged local PDFs; the local PDFs are not available in the repository connector or this execution environment.

- **KYC q06:** paragraph 55, Secrecy Obligations and Sharing of Information, states the secrecy/confidentiality rule and its exceptions. The question's target is supported.
- **KYC q07:** paragraph 56(b) specifies CKYCR upload within 10 days of commencement of an account-based relationship.
- **KYC q05:** paragraph 40 begins in the Enhanced Due Diligence section; its listed non-face-to-face controls continue across the next page. The two-page target is appropriate at source level.
- **KYC q14:** paragraph 41 specifies PEP identification controls, source-of-funds/wealth measures, senior-management approval and ongoing enhanced monitoring. The question is distinct from q05.
- **KYC q09:** paragraph 64 begins with cross-border originator/beneficiary information and continues into responsibilities and further obligations. The broad four-page range needs exact local page confirmation; do not narrow it based on a snippet alone.
- **KYC q16–q20:** Annex IV begins on the source PDF's Annex IV pages. The constitutive-documents, proof-of-address, photographs, UBO identity, and authorized-signatories rows are present. q17's Category III proof-of-address cell explicitly excludes Power of Attorney; q18's photograph exemption has a footnote; q20 has category-specific Global Custodian language. Preserve these qualifications in answer keys.
- **Digital Lending q21:** paragraph 2 states outsourcing to an LSP/DLA does not diminish the RE's obligations.
- **Digital Lending q22:** the circular's transition clause gives REs until November 30, 2022 for existing digital loans to comply.
- **Digital Lending q23:** Annex I paragraph 4.1 assigns LSP fees/charges to the RE, not directly to the borrower.
- **Digital Lending q24:** Annex I paragraphs 5.2.1–5.2.3 require a standardized KFS before contract execution and specify its contents, including APR, recovery mechanism, grievance redressal contact, and cooling-off/look-up period.
- **NBFC filing q25:** the commercial-bank table on source PDF page 1 states five working days from the auditor-report signing date.

These are source-content confirmations, not visual inspection findings. In particular, browser-extracted PDF text cannot establish that the local PDF's rendered table layout, OCR output, or cleaned text preserves the same associations.
### Current audit conclusion

The metadata and semantic/category audit passes. No CSV correction is justified by the evidence currently available. **The gold set is not yet fully page-validated:** local PDF page alignment remains outstanding for all 25 records, including records with official-source checks. q17 also retains a specific table-cell association caveat. Do not rerun or overwrite the benchmark merely because this review was expanded; rerun only if a verified gold document/page label changes.
## Per-question evidence log

| ID | PDF page verified? | Printed page / section | Evidence description | Label accepted? | Reviewer note |
|---|---|---|---|---|---|
| q04 | Yes | PDF 38 / printed 37 / Part IV - Identification of Beneficial Owner | Paragraph 34 addresses identifying and taking reasonable steps to verify beneficial owners when opening an account for a legal person. | Yes, provisional | Exact passage begins on PDF page 38. The table of contents lists the section at printed page 38, but the section heading itself appears on printed page 37; evaluation metadata is PDF-index based. |
| q13 | Yes | PDF 69–70 / printed 68–69 / Paragraph 70, Hiring of Employees and Employee training | Paragraph 70 requires screening, appropriate staff attributes, ongoing KYC/AML/CFT training, differentiated training focus for frontline/compliance/new-customer staff, and trained audit staff. | Yes, provisional | The training paragraph continues across the printed-page boundary; PDF page 70 is the correct evaluator page for the retrieved passage. |
| q15 | Yes, source text | PDF 58–59 / printed 57–58 / Paragraph 56(j), CKYCR retrieval | An RE should retrieve KYC records through the customer's KYC Identifier and should not require resubmission of the same records or additional identification details unless one of the specified exceptions applies: changed customer information, incomplete/outdated or non-compliant records, expired document validity, or a need for identity/address verification, enhanced due diligence, or risk profiling. | Yes, provisional | Replaces a near-duplicate of q06. Local PDF page alignment must still be confirmed against the exact corpus file. |
| q16 | Yes | PDF 94 / Annex IV, Entity Level | Constitutive documents (including memorandum and articles of association and certificate of incorporation) are marked Mandatory for Categories I, II, and III. | Yes, provisional | The question specifically asks about Category I; the row confirms Mandatory. |
| q17 | Yes | PDF 94 / Annex IV, Entity Level | Entity-level proof of address is Mandatory for Category III, with the explicit qualification “other than Power of Attorney”. | Yes, provisional | Answer is yes, but retain the PoA exclusion. |
| q18 | Yes | PDF 95 / Annex IV, Senior Management | Photographs are marked Exempted for all three FPI categories; the asterisk note says starred documents are not required while opening the bank account, though they may be supplied on demand. | Yes, provisional | Preserve the footnote; do not imply the documents can never be requested. |
| q19 | Yes | PDF 95 / Annex IV, Ultimate Beneficial Owner | UBO proof of identity is Exempted for Categories I and II and Mandatory for Category III. | Yes, provisional | Question now explicitly identifies the UBO row to avoid ambiguity with entity-level or senior-management proof of identity. |
| q20 | Yes | PDF 95 / Annex IV, Authorized Signatories | The authorized-signatories list and signatures are Mandatory for Category III. Categories I and II permit the Global Custodian signatory list when there is a PoA to the Global Custodian. | Yes, provisional | Question now names Category III and the exact row; the Category I/II caveat belongs in the answer. |

| q25 | Yes | PDF 1 / revised filing requirements, commercial-bank row | The first page states that all audited returns for commercial banks are due within five working days from signing of the Auditor’s report. | Yes, narrowed | The original question was overbroad. It is now explicitly scoped to commercial banks and “all audited returns”. The separate NBFC filing table has different periodicity-based timelines; do not conflate them. |
\nQuestions q01–q03, q05–q12, and q14 still require local corpus page verification; q01 and q14 have distinct, source-grounded target passages. q02 and q03 are now deliberately separated: q02 targets paragraph 13's identification triggers on PDF page 22; q03 targets paragraph 14's conditions for relying on third-party CDD on PDF pages 22–23. These passages are adjacent in the source but test different obligations. Confirm the exact page split against the local corpus PDF. The official RBI notification page and an accessible copy of the original circular provide source text for q21–q24; however, the local corpus PDF page alignment still needs confirmation before the gold page ranges are accepted. Do not treat this register as a completed gold-set audit.

## Remaining KYC question review (semantic/source-text pass)

The official RBI Master Direction page and PDF for the August 14, 2025 consolidated version were checked for the subject matter and printed/PDF page mapping of the remaining KYC questions. This is a **content-level review only**; it does not establish that the current local corpus PDF contains each passage on the evaluator's recorded page range. Those page ranges remain provisional until checked against the exact local PDF.

| ID | Topic checked | Content-level assessment | Page-alignment status |
|---|---|---|---|
| q01 | Existing KYC-compliant customer opening another account/service at the same RE | Paragraph 10(f) says an existing KYC-compliant customer need not submit KYC documents again for another account/product/service with the same RE unless identity/address information has changed. RBI's June 2025 KYC FAQ confirms the same exception. | Printed page 18 / proposed PDF page 19; official source mapping confirmed; local corpus page check required |
| q02 | Circumstances requiring customer identification | Paragraph 13 lists triggers: commencement of an account-based relationship, international money transfer for a non-account-holder, doubts about authenticity/adequacy of identification data, specified product/agent transactions over ₹50,000, qualifying walk-in transactions, and suspected structuring below the threshold. | Printed page 21 / PDF page 22; official PDF page mapping confirmed; local corpus copy check remains required |
| q03 | Third-party CDD reliance conditions | Paragraph 14 permits an RE to rely on third-party CDD only when it immediately obtains the CDD records/information, can obtain supporting identification documents without delay, the third party is regulated/supervised and compliant with PML recordkeeping, the third party is not based in a high-risk jurisdiction, and ultimate CDD/EDD responsibility remains with the RE. | Printed pages 21–22 / proposed PDF pages 22–23; official source mapping confirmed; local corpus page split remains to be checked |
| q05 | Enhanced due diligence | Paragraph 40 sets EDD controls for non-face-to-face onboarding: offer V-CIP first where available, restrict post-onboarding alternate mobile numbers for transaction OTP/updates, verify current address by positive confirmation, obtain/verify PAN, require first credit from an existing KYC-compliant bank account, and apply high-risk classification and enhanced monitoring. | Paragraph 40 starts on printed page 44 and continues through printed page 45; proposed evaluator PDF pages 45–46. Exact local page check remains required |
| q06 | Confidentiality of customer information | Distinct from q15 after q15 was changed to CKYCR resubmission exceptions. | Provisional; local PDF check required |
| q07 | Initial CKYCR upload deadline | Paragraph 56(b) specifies upload within 10 days of commencement of an account-based relationship. This is an initial-upload requirement. | Provisional; local PDF check required |
| q08 | Action after CKYCR updates an existing record | Paragraph 56(h) requires retrieval of updated records after CKYCR notification and updating the RE's own record. Distinct from q07's initial upload and q15's resubmission restrictions. | Provisional; local PDF check required |
| q09 | Cross-border wire-transfer information | Paragraph 64 requires accurate, complete originator and beneficiary information for cross-border wire transfers: originator name, account number where used, address or specified identity/customer/date-and-place-of-birth alternative, beneficiary name, and beneficiary account number where used; a unique transaction reference is required where there is no account. The paragraph also covers batch transfers and qualifying domestic transfers. | Printed pages 63–66; evaluator PDF pages 64–67. Range corrected by the established +1 PDF-page offset; exact local copy check remains required |
| q10 | PAN or Form 60 | Paragraph 66 requires PAN or equivalent e-document to be obtained and verified for transactions under Income Tax Rule 114B applicable to banks; Form 60 is obtained from persons without PAN/equivalent e-document. | Printed page 67 / PDF page 68; official PDF page mapping confirmed; local corpus copy check remains required |
| q11 | Digital KYC application controls | Annex I clauses A–B require an authenticated RE application at customer touch points and restrict access to authorized officials through RE-controlled login/password or Live OTP/Time OTP. | Printed page 70 / PDF page 71; source page mapping confirmed; local copy check remains required |
| q12 | OTP in digital KYC | Annex I clause I sends an OTP to the customer's own mobile number; successful validation is treated as the customer's signature on the Customer Application Form. The authorized officer's registered mobile number must not be used for the customer signature. This is distinct from q11's official access-control mechanism. | Printed page 71 / PDF page 72; source page mapping confirmed; local copy check remains required |
| q14 | Politically exposed persons (PEPs) | Paragraph 41 permits establishing/continuing a PEP relationship subject to additional controls: PEP identification, source-of-funds/wealth measures, senior-management approval, and enhanced ongoing monitoring; the rules also extend to family members and close associates. | PDF page 47 / printed page 46 / paragraph 41; source page verified, local corpus page confirmation remains required |

### Redundancy risks to resolve during local page review

- **q01/q03:** The overlap has been addressed. q01 now tests the same-RE repeat-account exception in paragraph 10(f); q03 continues to test the customer identification procedure. Confirm the proposed q01 PDF page locally.
- **q05/q14:** The overlap has been addressed by changing q14 to the distinct PEP-specific controls in paragraph 41. Confirm the proposed q14 PDF page locally.
- **q07/q08/q15:** These are now three separate CKYCR operations: initial upload, responding to an updated record, and exceptions to re-requesting documents. Keep the distinctions explicit in answer keys.
- **q11/q12:** Related digital-KYC topics, but application security controls and OTP authentication are not interchangeable. Verify that their source passages are materially distinct.

## Source-version caveats

- The RBI KYC PDF in the corpus is the Master Direction dated February 25, 2016, **updated as on August 14, 2025**. The PEP provision in paragraph 41 is printed on page 46; with the established one-page offset in this PDF, its evaluator page is 47. The manifest now records `issue_date=2016-02-25` and `updated_as_of=2025-08-14`. The historical `doc_id` remains `rbi_kyc_2024` to preserve compatibility with existing indexed metadata; it is a legacy identifier, not the document issue year. The RBI subsequently repealed the 2016 Master Direction with immediate effect on November 28, 2025 for Payment System Providers and Payment System Participants, and issued entity-specific 2025 KYC Directions. Treat this corpus PDF as a historical consolidated snapshot, not a current universal KYC rulebook.
- The Digital Lending Guidelines dated September 2, 2022 are retained as a historical source for this test set. RBI issued the consolidated Digital Lending Directions, 2025 on May 8, 2025; do not present the 2022 document as current policy.
- A retrieval hit is judged against the selected gold document/page only; an equivalent answer in a later or superseding circular is not counted unless explicitly added to the gold set.

## CKYCR source check (q15)

The August 14, 2025 consolidated RBI KYC Master Direction states in paragraph 56(j) that an RE should obtain the customer's KYC Identifier and retrieve KYC records from CKYCR rather than require the customer to resubmit the same records or additional identification details, subject to the four stated exceptions. The passage begins on printed page 57 and continues onto printed page 58. The question now targets this distinct rule instead of duplicating q06's secrecy obligation. The proposed evaluator range is PDF pages 58–59 based on the document's printed-page offset; verify this against the exact local corpus PDF before final acceptance.

## Digital Lending source check (q21–q24)

The RBI notification dated September 2, 2022 confirms that the 2022 Guidelines required REs to retain responsibility despite outsourcing to LSPs/DLAs (paragraph 2), gave until November 30, 2022 for existing digital loans to comply (paragraph 3), and required LSP fees/charges to be paid by the RE rather than directly by the borrower (Annex I, paragraph 3.2). The KFS disclosure requirement is in Annex I, paragraph 5.1. These are historical requirements: RBI's official Master Directions page explicitly marks the 2022 circular repealed and directs readers to the Digital Lending Directions, 2025. The local corpus PDF is 12 pages; the precise evaluator page mapping for q21–q24 still requires checking against that exact file.



## Local PDF audit correction — 2026-11-07

- **q14 corrected:** the PEP controls in paragraph 41 are on KYC PDF page 46, not page 47. `eval/questions.csv` now records `expected_page_start=46` and `expected_page_end=46`.
- **q13 remains under review:** the exported PDF page 70 begins mid-sentence in the staff-training passage. PDF page 69 was not included in the export, so the exact local gold range cannot yet be finalized. Export and inspect page 69 before deciding whether q13 should cover pages 69–70.
- The corrected q14 gold label changes the benchmark target. Rerun the retrieval benchmark after q13's page range is finalized; do not compare the new run as if the gold set were unchanged.


- **q13 finalized:** the local KYC PDF page 69 begins paragraph 70, “Hiring of Employees and Employee training,” including screening, staff qualifications, and the start of the ongoing-training requirement. Page 70 continues the training provisions. The gold range is therefore **69–70**, not 70 alone.
