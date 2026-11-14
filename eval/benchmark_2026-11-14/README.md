# Task 1: Retrieval quality evaluation (2026-11-14)

## Status

| Part | State |
|---|---|
| Gold-set validation against the 37 PDFs | Done. Report: `dataset_validation_report.md` |
| Extended, validated gold set (v2) | Done. `gold_questions_v2.csv` (42 questions, 41 usable) |
| Metrics code, benchmark runner, unit tests | Done and tested with fixtures |
| **Benchmark on `policylens_v1_fixed` / `policylens_v1_structure`** | **Not run.** See "Why the benchmark has not run" |
| Qualitative error analysis, recommendation | **Pending the benchmark.** Nothing below is a result |

## Why the benchmark has not run

The session that produced this work had the repository and the 37 PDFs but not the Chroma database (`chroma_db/` is gitignored), and it could not reach Hugging Face to load `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`. Rebuilding an index in that environment would have meant re-ingesting the corpus, which the task forbids without review, and it would not have been the audited 5,932 / 15,773-record collections. No benchmark numbers exist, and none are estimated here.

## Methodology

Relevance uses document ID and inclusive 1-based PDF page range. A retrieved chunk is relevant to a gold passage when `doc_id` matches and its `page_start`..`page_end` overlaps the passage range. A chunk is relevant to a question if it matches any of its gold passages.

| Metric | Definition |
|---|---|
| Hit Rate@k | 1 if any of the top k is relevant. The legacy `evaluate.py` labels this "Recall@k" |
| Recall@k | Fraction of the question's gold passages covered by the top k. Equals Hit Rate@k for single-passage questions |
| Precision@k | Relevant results in the top k divided by k (k is the denominator even if fewer results return) |
| MRR | Mean of 1/rank of the first relevant result, 0 if none in the top 10 |

Held constant across strategies: query text, a single set of query embeddings reused for both collections, `config.yaml` embedding settings, top-k 10, no metadata filter, the same Chroma `query` call, the same question set. Only the collection name differs.

The score in the log is cosine similarity (`1 - distance`); Chroma's cosine distance is also logged. Lower distance means closer.

Safety: the runner copies the Chroma directory to a temporary location and queries the copy. It hashes the original directory before and after and records the result in `run_metadata.json`. It uses `get_collection`, never `get_or_create_collection`, and refuses to write into a non-empty output directory.

## Gold-set validation summary

All 37 PDFs match `data/pdf_checksums.csv` and the manifest page counts. The existing validator and its tests pass. Every gold passage in v2 was checked against the PDF text of its page range (45 passage checks, 0 failures; the scanned 1981 gazette was checked by Tesseract OCR). The 25 original IDs, questions and v1 page ranges are preserved in the v2 file.

| ID | Finding | Action |
|---|---|---|
| q17 | v1 range 94-95 over-inclusive; the Category III entity proof-of-address cell is on p94 only | v2 passage 94-94 (corrected) |
| q19, q20 | Row is on p95 but the Category column headers are on p94; p95 rows carry no category labels | v2 needs two passages, 94 and 95 (corrected) |
| q21 | v1 range 1-4; the only passage saying RE obligations are not diminished is circular para 2 on p1 | v2 passage 1-1 (corrected) |
| q23 | v1 range 4-5; para 4.1 is on p4, p5 para 5.2.3 is a different fee rule | v2 passage 4-4 (corrected) |
| q05 | Wording is generic; only para 40 is headed Enhanced Due Diligence, and p46 also starts para 41 (PEPs, q14) | Kept, flagged in notes |
| q09 | Four-page span, scored leniently | Kept, flagged |
| x04 | Scanned gazette, no native text | Kept; retrieval depends on ingestion OCR |
| x05 | PDF p27 is an almost empty "Annexure 2" page; no text lists benefits of video-based identification anywhere in the document | Invalid, excluded from headline |

Twelve questions were added (q26-q37) from passages read in the PDFs: periodic-updation intervals, small-account and OTP e-KYC limits, DPDP breach timing, consent-manager net worth, DPDP commencement dates, cooling-off period, penal interest, digitally signed documents, a PFRDA vs RBI V-CIP definition pair, and a three-passage distinction question (q37).

Coverage of the 41 usable questions: direct 31, paraphrase 9, table 5, numeric or date 12, clause-specific 19, distinction 6, multi-passage 3 (q19, q20, q37). By document: RBI KYC 25, Digital Lending 7, DPDP Rules 5, and one each for NBFC filing, PFRDA, SEBI research analysts and the 1981 gazette.

## Limitations

- Gold questions cover 7 of the 37 documents (RBI KYC, Digital Lending, NBFC filing; DPDP Rules; SEBI research analysts; PFRDA; the 1981 gazette). The SEBI master circulars, HFC directions and Supreme Court chronicles are barely represented. Results will not generalise to the whole corpus.
- The questions were written after ingestion began, so this is not a blind holdout, and the original 25 are 80% KYC.
- Only 3 multi-passage questions exist, so passage-level Recall@k differs from Hit Rate@k on very few cases.
- Evidence checks use phrase matching against page text. They prove the phrase is on the labelled pages, not that the question is perfectly answerable from them.
- Relevance is page-overlap based. A chunk on the right page but from a different clause counts as relevant (q05/q14 on p46; q23/q32 on p4).
- 41 questions give wide confidence intervals; the runner writes a paired bootstrap, and small differences should not be read as superiority.
- This evaluates retrieval only, not answer quality.

## Reproduce

Validate the dataset (needs the PDFs and `pymupdf`; add Tesseract for the scanned gazette):

```bash
PYTHONPATH=. python eval/validate_gold_v2.py --pdf-dir data/pdfs --ocr --report eval/benchmark_2026-11-14/dataset_validation_report.md
```

Run the benchmark (needs the local Chroma database and the embedding model; writes to a new `eval/benchmark_<date>_run/` directory):

```bash
PYTHONPATH=. python eval/run_retrieval_benchmark.py --db-path "<path to chroma_db>" --collection-base policylens_v1
```

Unit tests (no Chroma database or model needed):

```bash
PYTHONPATH=. python -m pytest -q tests/test_retrieval_metrics.py tests/test_gold_set_validation.py tests/test_eval_tools.py
```

## Results

Not yet available. The run writes `retrieval_log.csv`, `metrics.csv`, `per_question.csv`, `paired_bootstrap.json`, `cases_for_inspection.md` and `run_metadata.json`.

## Hypotheses to check once results exist

These come from reading the source pages, not from retrieval output.

- q19 and q20 may fail or rank poorly for any chunking that splits the Annex IV table between p94 (headers) and p95 (rows).
- q34 and q35 are near-identical questions about different regulators; wrong-document hits are a likely failure mode.
- q23 and q32 are adjacent clauses on p4, and q05 and q14 share p46; page-overlap scoring will not separate them.
- x04 depends entirely on the quality of OCR text in the index.
