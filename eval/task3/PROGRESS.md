# Task 3 review progress

Last updated: 2026-11-15. Branch: `task3-answer-key-verification` (off `task3-answer-validation` @ 7ac6890).

## Done
- Answer key: all 41 valid questions (q01-q37, x01-x04) checked against the source PDF pages and set to `annotation_status=verified`.
  - Method: page text from `pdftotext -layout`; the FPI table (q16-q20, RBI KYC pp94-95) and the scanned 1981 gazette page (x04) were also read as page images.
  - Every row's `review_notes` records the paragraph and page checked and what was corrected.
- Validator on the answer key: no answer-key errors. All remaining errors are the blank evidence-review rows.
- Unit tests: `tests/test_answer_validation.py` 6 passed.

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

## Not done (blocked: needs your local Chroma DB)
- Evidence review of the 820 retrieval rows (`evidence_class`, `supported_fact_ids`, `citation_status`, `source_verified`). The retrieval log holds only ~190-character previews, and full chunk text exists only in the local Chroma DB.
- Therefore: no scoring, no results report, and the evidence-review CSV is untouched (all rows still blank).

## Next step
Run locally, then commit the output file to this branch or send it over:

    ./.venv/bin/python eval/task3/export_chunk_text.py

This writes `eval/task3/chunk_text.jsonl` (read-only on Chroma; refuses to overwrite). Evidence rows are then reviewed per question against the verified key, in batches.
