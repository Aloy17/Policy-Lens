# PolicyLens

PolicyLens is a local PDF ingestion and retrieval system for regulatory circulars and policy documents. It extracts page-level text, applies OCR fallback to candidate scanned pages, cleans extracted content, creates fixed-size and structure-aware chunks, embeds them locally, and indexes them in ChromaDB. A Streamlit interface and CLI retrieve passages with document, page and section traceability.

**Scope:** PolicyLens is a retrieval system. It does not generate legal answers, provide legal advice, or certify that a regulatory instrument is currently in force.

## Project report

The six-page technical report is available at [report/PolicyLens_Report.pdf](report/PolicyLens_Report.pdf). It describes the architecture, design decisions, evaluation results, parsing limitations, scaling approach, circular lifecycle handling, and privacy controls.

## Standalone macOS application (Apple Silicon)

A portable ARM64 macOS build is documented in [packaging/README.md](packaging/README.md). The generated `dist/PolicyLens/` folder contains `PolicyLens.app` and a sibling `PolicyLens Data/` folder. Keep them together. The app is unsigned; consult the packaging guide for first-launch and distribution limitations.

## Development installation

Requirements:
- Python 3.10+
- Tesseract OCR
- Git

```bash
git clone https://github.com/Aloy17/Policy-Lens.git
cd Policy-Lens
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ui.txt
```

On macOS, install Tesseract with `brew install tesseract`. On Ubuntu/Debian use `sudo apt install tesseract-ocr`. On Windows, install Tesseract and add it to PATH.

## Corpus and indexing

The corpus inventory and source metadata are in `data/manifest.csv`; corpus annotations are in `data/corpus_annotations.csv`. The corpus contains 37 source PDFs under `data/pdfs/`. Check each source's reuse and redistribution terms before redistributing the repository or repackaging the PDFs; public accessibility alone does not grant redistribution rights.

To refresh the corpus report:

```bash
python3 data/build_corpus.py
```

The annotations record observed table evidence, layout evidence and a mutually exclusive `primary_corpus_category` for the approximate corpus-mix calculation. The manifest's `document_type` is the technical extraction classification (`text_native` or `scanned_or_mixed`); a text-native PDF may also contain tables or use a two-column layout.

Build or update the vector index:

```bash
python ingest.py --input data/pdfs --manifest data/manifest.csv --collection policylens_v1
```

The first run downloads the configured Sentence Transformers model unless a local model path is configured. ChromaDB data and logs are stored locally. Hash-based ingestion skips unchanged source documents.

**Recorded corpus run (2026-11-14):** 37 documents, 5,050 pages, 217 OCR pages, 5,932 fixed-size chunks and 15,773 structure-aware chunks. These are the recorded results for that run; a fresh local ingest may differ if the corpus or configuration changes.

## Ingestion design

See [docs/ingestion_design.md](docs/ingestion_design.md) for parser, OCR, cleaning, chunking, embedding and vector-index decisions.

## Search

CLI example:

```bash
python search.py "cash disbursement limit for secured loans" --top_k 5 --filter issuer=RBI
```

Use repeated `--filter KEY=VALUE` arguments for additional metadata constraints. To launch the graphical interface:

```bash
streamlit run ui/app.py
```

The CLI supports metadata filters; the Streamlit interface currently does not expose filter controls. Search results include document title, page range, section and a passage preview.

## Evaluation

The repository contains three distinct evaluation workstreams. Their metrics answer different questions and should not be combined into a single accuracy score.

### Task 1 — retrieval quality

The expanded benchmark dated 2026-11-14 evaluated 41 valid questions against fixed-size and structure-aware collections using top-10 retrieval. The 42-row dataset had one invalid question excluded. It covers 7 of the 37 corpus documents and is weighted toward RBI KYC.

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Page-overlap MRR | 0.4978 | 0.5983 |
| Page-overlap Recall@10 | 0.7805 | 0.8089 |
| Lexical-proxy MRR | 0.2542 | 0.2834 |
| Lexical-proxy Recall@10 | 0.4634 | 0.3943 |
| Indexed chunks | 5,932 | 15,773 |

Page-overlap relevance requires a matching document and overlapping PDF page range. The lexical proxy additionally requires all terms in a gold passage's term group to occur in the retrieved chunk. Neither proxy is a semantic answer-quality measure. Paired-bootstrap 95% confidence intervals include zero for the reported comparisons, so this run does not establish a statistically conclusive winner.

The expanded benchmark report, methodology, dataset validation, and limitations are in [eval/benchmark_2026-11-14/](eval/benchmark_2026-11-14/). The earlier 25-question benchmark and its corrected rerun remain documented separately in [eval/benchmark_run_2026-11-07.md](eval/benchmark_run_2026-11-07.md). Gold-set chronology and later question/page corrections are disclosed in [eval/gold_set_history.md](eval/gold_set_history.md). The expanded 41-question run is supplementary evidence, not an untouched blind holdout.

### Task 2 — extraction fidelity

Task 2 evaluates extraction behavior separately from retrieval ranking. The evidence includes selected-page regression checks, a ten-page manual extraction sample, and a two-page manually transcribed OCR pilot. The pilot measured 82.37% micro word accuracy across 675 reference words; this is too small to represent corpus-wide OCR accuracy.

The seven-page automated evaluator and OCR scorer are documented in [eval/extraction_fidelity_findings.md](eval/extraction_fidelity_findings.md). GitHub Actions runs these checks, but local reruns and several real-PDF visual checks remain outstanding: the S03, S05, S06 and S07 pages, plus a representative real two-column page. Automated keyword/presence checks do not establish correct table-cell or row relationships.

### Task 3 — retrieved evidence support and citation fidelity

Task 3 manually reviewed the top 10 retrieved chunks for 41 questions under both strategies: 820 chunk assessments in total. All 54 source pages flagged for visual review were inspected using the committed contact sheets, and all 820 citation assessments were marked accurate against their source pages.

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Complete answer-fact support | 19/41 (46.3%) | 25/41 (61.0%) |
| Partial answer-fact support | 5/41 (12.2%) | 5/41 (12.2%) |
| No required-fact support in top 10 | 17/41 (41.5%) | 11/41 (26.8%) |
| Mean required-fact coverage | 53.3% | 67.2% |

These are human-reviewed evidence-support results for this question set and retrieval configuration, not generated-answer accuracy or a general guarantee of retrieval performance. Important source-currency caveats—including the superseded 2022 RBI Digital Lending circular and the historical Special Bearer Bonds Ordinance—are recorded in the report.

See [eval/task3/REPORT.md](eval/task3/REPORT.md) for the protocol, results, limitations and reproduction commands; [eval/task3/PROGRESS.md](eval/task3/PROGRESS.md) records the review status.

## Tests

Run the automated test suite:

```bash
python -m pytest -q
```

The repository's GitHub Actions workflows also run the configured test and evaluation checks. See [`.github/workflows/`](.github/workflows/) for the workflow definitions. A passing automated test suite does not replace manual source-PDF inspection or the evaluation limitations documented above.

## Known limitations

- Table extraction and reconstruction can lose numeric fidelity or table-cell relationships. Verify high-impact numeric values against the original PDF.
- OCR accuracy is measured only on a two-page pilot; it is not a corpus-wide estimate.
- Real-PDF visual verification of selected table/layout cases and a representative two-column page remains incomplete.
- Task 1's expanded gold set covers only 7 of 37 documents, is non-blind, and uses page-overlap and lexical relevance proxies.
- Task 3 measures human-reviewed support in retrieved passages; it does not evaluate answer generation or legal correctness.
- Some evaluated source instruments are historical or superseded. Retrieval against them must not be interpreted as current regulatory guidance.
- Public availability of a source PDF does not automatically grant redistribution rights.
