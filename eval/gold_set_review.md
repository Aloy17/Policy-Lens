# Gold-set review register

Status: **pending source-page verification**.

The canonical questions are in `questions.csv`. This register deliberately does not claim that page references or category labels have been manually validated. The evaluator's overlap rule is inclusive and uses PDF page indices as stored in chunk metadata; confirm the exact page convention against the source PDF before accepting a gold label.

| Review item | Current state | Required action |
|---|---|---|
| Question count | 25 records | Confirm unchanged after review |
| Table questions | 5 labels (q16–q20) | Confirm each answer depends on a table cell/value |
| Paraphrased questions | 5 labels (q02, q08, q14, q21, q23) | Compare source wording and query wording; revise weak labels |
| Gold document IDs | Three RBI documents | Confirm exact document version and title |
| Gold page ranges | Populated for all 25 | Open each PDF page and record evidence below |
| Page convention | 1-based PDF page indices assumed | Verify printed page numbers where they differ |

## Per-question evidence log

For each question, record the exact section/table heading and a short description of the evidence found on the cited page. Do not copy long source passages into this file.

| ID | PDF page verified? | Printed page / section | Evidence description | Label accepted? | Reviewer note |
|---|---|---|---|---|---|
| q01–q25 | Pending | Pending | Pending | Pending | Complete individually; do not treat this range as one review entry |

## Known source-version caveats

- The KYC Master Direction PDF in the manifest may be a consolidated version with later amendments. Preserve the original issue date and record the PDF's actual consolidation/as-of date separately after verifying the document cover/footnotes.
- The Digital Lending Guidelines dated 2022 are retained as a historical source for this test set. RBI's 2025 Digital Lending Directions supersede the earlier framework for current-policy interpretation.
- A retrieval hit is judged against the selected gold document/page only; an equivalent answer in a later or superseding circular is not counted unless explicitly added to the gold set.
