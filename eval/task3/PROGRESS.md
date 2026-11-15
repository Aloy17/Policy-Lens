# Task 3 review progress

Last updated: 2026-11-15. Branch: `task3-answer-key-verification` (off `task3-answer-validation` @ 7ac6890).

## Done
- Answer key: all 41 valid questions (q01-q37, x01-x04) checked against the source PDF pages and set to `annotation_status=verified`.
  - Method: page text from `pdftotext -layout`; the FPI table (q16-q20, RBI KYC pp94-95) and the scanned 1981 gazette page (x04) were also read as page images.
  - Every row's `review_notes` records the paragraph and page checked and what was corrected.
- Validator on the answer key: no answer-key errors. All remaining errors are the blank evidence-review rows.
- Unit tests: `tests/test_answer_validation.py` 6 passed.
- Full retrieved chunk text and cited source-page text exports were supplied; no local Chroma access is required for text-level analysis.
- Added `audit_chunk_sources.py`, a read-only diagnostic comparing retrieved chunk text to its cited source-page text.
- Audit results: all 820/820 cited page ranges are present in the supplied source-page export; 517 chunks have >=0.95 text alignment, 168 have 0.80-0.95, 81 have 0.50-0.80, 25 have 0.01-0.50, and 29 have 0.00.
- 154 chunks cite at least one page flagged for visual review in the source-page export.
- Added `source_alignment_summary.json` and `source_alignment_report.md`. These are text-alignment diagnostics only, not semantic evidence review or source-PDF visual verification.

## Material corrections to the draft key
- q01: removed conditions not in the text (address change, retrievable record). Source: para 10(f), p19.
- q02: replaced placeholder F4 with the actual six triggers (para 13(a)-(f)).
- q03: added missing condition that the third party must not be in a high-risk jurisdiction (para 14(d)).
- q04: thresholds and senior-managing-official fallback are in para 3(a)(iv), pp5-6, not the gold page 38. Gold supplemented.
- q08: para 56(h) spans pp58-59; added the 7-day onward-furnishing duty.
- q09: the information list is on p63 (gold 64-67 missed it). Gold supplemented.
- q31: exit mechanism and minimum 3-day / 1-day periods are in para 8 on p7, not gold p3. Gold supplemented.
- q34, q35: removed unsupported wording; aligned to the definitions (audit trail, independent verification).
- x02: trigger corrected to the Third Schedule non-engagement period.
- x04: instrument is an Ordinance; wording is "nature and source of acquisition", not "manner or consideration". Page carries a handwritten "Repealed" note.
- q19, q20: gold narrowed to p95 (UBO and authorised-signatory rows are on p95 only).

## Currency flags (not errors in the key)
- The RBI digital lending circular (q21-q24, q31-q33) has a banner on p1: repealed, replaced by the RBI (Digital Lending) Directions, 2025.
- x03: a separate `sebi_master_circular_for_research_analysts_2026` PDF exists; not compared with the cited document.

## Not done
- Human semantic review of all 820 retrieval rows: `evidence_class`, `supported_fact_ids`, `citation_status`.
- Visual inspection of all original cited PDF pages; the 154 flagged rows/pages need particular attention, with table/scanned pages checked carefully.
- Scoring and final Task 3 results report. The scoring script requires every review row to have a defensible manual annotation and accurate citations to be source-verified.

## Important review boundary
The text-alignment audit does not determine whether a chunk supports any required fact, whether a citation is semantically correct, or whether a table/scanned page was visually read. Do not populate the evidence-review CSV or set `source_verified=yes` from alignment alone.

## Next step
Continue the human evidence review in question batches using `chunk_text.jsonl`, the verified answer key, and original PDF pages. Use `audit_chunk_sources.py` to prioritize low-alignment and visual-review cases. The audit script does not access or mutate Chroma or source PDFs.
