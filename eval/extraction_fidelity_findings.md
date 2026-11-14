# Task 2 — extraction fidelity findings

## Scope

This phase examines extraction fidelity separately from retrieval ranking. The current evidence is a ten-page manual extraction sample, two manually transcribed OCR reference pages, and deterministic regression checks added for selected PDF pages. It is not a corpus-wide accuracy study.

## Existing sampled-page findings

| Sample | Document / PDF page | Existing observation | Status for this phase |
|---|---|---|---|
| S03 | SEBI Depositories, p. 170 | Source/native text and cleaned text show the medium-risk multiplier as `1.5`, while the serialized table showed `15 .`. | Parser now protects decimal values from conflicting positioned-word reconstruction. Must rerun the new page check locally. |
| S05 | SEBI LODR 2026, p. 82 | Wide multi-level shareholding table has fragmented headers and difficult column relationships. | Automated presence checks only; visual column mapping remains open. |
| S06 | SEBI LODR 2026, p. 213 | Native text and table output include the cross-reference “Principle 6, Question 7 of Essential Indicators”; cleaned prose omitted part of it. | Preserve table text as an additive extraction path; verify final table chunks and visual source page. |
| S07 | SEBI Merchant Bankers, p. 104 | Circular numbers, dates and subjects are difficult to associate from serialized text. | Automated presence checks only; visual row association remains open. |
| S08 | SEBI Mutual Funds, p. 217 | Three InvIT limits and remarks are represented coherently in the table output. | Regression case added for all three distinct limits. |

These findings originate in the existing sampled-page inspection record. Visual verification of S03, S05, S06 and S07 was not completed in that inspection; do not describe those observations as visually confirmed.

## OCR reference baseline

The committed OCR score file contains two manually transcribed page references:

| Document / page | Reference words | Word errors | WER | Word accuracy |
|---|---:|---:|---:|---:|
| Special Bearer Bonds Gazette, p. 2 | 471 | 49 | 10.40% | 89.60% |
| PFRDA KYC/AML/CFT circular, p. 27 | 204 | 70 | 34.31% | 65.69% |

Across the 675 reference words, the aggregate micro word accuracy is 82.37% (119 edit errors / 675 reference words). This is a two-page pilot only; it is too small and too document-specific to support a corpus-wide OCR accuracy claim. Exact whitespace-token WER is sensitive to punctuation and transcription conventions.

## Automated checks added

Run the selected-page extraction checks:

```bash
PYTHONPATH=. python eval/extraction_fidelity.py \
  --pdf-dir data/pdfs \
  --output eval/extraction_fidelity_report.json
```

The seven-page set checks:
- decimal and label fidelity in the SEBI Depositories risk table;
- presence of key headers in the wide LODR table;
- BRSR cross-reference text;
- Merchant Banker rescinded-circular table terms;
- all three InvIT investment limits;
- two scanned/mixed pages through the production OCR fallback.

Run OCR accuracy independently against the manually transcribed references:

```bash
PYTHONPATH=. python eval/ocr_accuracy.py \
  --reference-dir eval/ocr_reference \
  --pdf-dir data/pdfs \
  --output eval/ocr_accuracy.csv
```

The fidelity runner does not claim to validate semantic table-cell relationships. The wide LODR table and Merchant Banker table still require visual review. The OCR runner requires local Tesseract and the PDFs; the CI suite tests evaluator logic but does not download the corpus or execute OCR.

## Two-column layout

The existing parser has a synthetic regression test ensuring a center-gutter block is not duplicated and each column preserves top-to-bottom order. The current ten-page real-PDF sample does not establish performance on a representative two-column document. A real two-column source page still needs to be selected and visually checked before claiming real-document validation.

## Remaining work

1. Run the seven-page evaluator and OCR scorer against the local corpus PDFs with Tesseract installed.
2. Inspect the rendered S03, S05, S06 and S07 pages; record cell/row-level judgments, not only keyword presence.
3. Select at least one genuine two-column page and compare rendered reading order with extracted text.
4. Review failures and update parser/OCR logic only when the source page supports the correction.
5. Record exact commands, environment and outputs in the final evaluation report. Do not commit machine-specific paths or local Chroma/database artifacts.
