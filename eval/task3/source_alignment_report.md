# Task 3 source-page text alignment audit

Generated: 2026-11-15  
Inputs: the 820-record chunk-text export and 570 source-page records supplied for Task 3.  
Method: normalize chunk and cited-page text, then calculate the fraction of distinct chunk token trigrams also present in the cited source-page text. This is a diagnostic comparison only.

## Coverage

- Retrieved chunk records audited: **820**
- Cited source-page ranges fully present in the source-page export: **820/820**
- Chunks whose cited pages include at least one page flagged for visual review in the source-page export: **154**

| Alignment | Chunks |
|---|---:|
| 0.95–1.00 | 517 |
| 0.80–0.95 | 168 |
| 0.50–0.80 | 81 |
| 0.01–0.50 | 25 |
| 0.00 | 29 |

## Strategy comparison

| Strategy | Chunks | Alignment ≥0.95 | Alignment ≥0.80 | Alignment <0.50 | Mean alignment |
|---|---:|---:|---:|---:|---:|
| Fixed | 410 | 252 | 348 | 18 | 0.8996 |
| Structure-aware | 410 | 265 | 337 | 36 | 0.8719 |

These are text-to-source alignment diagnostics, not retrieval relevance or answer-support scores.

## Interpretation and limitations

- All 820 cited page ranges were represented in the supplied source-page export.
- 29 rows had zero token-trigram alignment. This can indicate extraction/OCR differences, very short structural chunks, or citation mismatch; it does not by itself prove an incorrect citation.
- 154 chunks cite at least one page flagged for visual review. Those pages need visual inspection before claiming source verification.
- This audit does not determine whether a chunk answers its question or supports any atomic required fact.
- It does not assign `evidence_class`, `supported_fact_ids`, or `citation_status`.
- It does not set `source_verified=yes`. The export's visual-review flag is not evidence that the original PDF page image was inspected in this audit.
- Text alignment cannot validate table row/column associations, headers, footnotes, scanned content, or supersession/currentness.

See `audit_chunk_sources.py` for the reproducible read-only audit. Detailed per-chunk output is generated as `source_alignment_audit.csv` when run locally with the two exports.
