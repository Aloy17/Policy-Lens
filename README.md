# PolicyLens

PolicyLens is a PDF ingestion and retrieval system for regulatory circulars and policy documents. It extracts page-level text, applies OCR fallback to candidate scanned pages, cleans extracted content, creates fixed-size and structure-aware chunks, embeds them locally, and indexes them in ChromaDB. A Streamlit interface and CLI retrieve passages with document, page and section traceability. Answer generation and legal advice are out of scope.

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

The corpus inventory and source metadata are in `data/manifest.csv`; corpus annotations are in `data/corpus_annotations.csv`. The current repository branch tracks the 37 source PDFs under `data/pdfs/`. Check each source's reuse and redistribution terms before redistributing the repository or repackaging the PDFs; public accessibility alone does not grant redistribution rights.

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

The CLI supports metadata filters; the Streamlit interface currently does not expose filter controls. Search results include document title, page range, section and a passage preview. This is a retrieval-only system, not an answer-generation or legal-advice system.

## Retrieval evaluation

The Phase 3 evaluation compares fixed-size and structure-aware chunking on the same 25-question gold set and embedding model. The latest benchmark record is [eval/benchmark_run_2026-11-07.md](eval/benchmark_run_2026-11-07.md); detailed protocol, metrics and interpretation limits are in [eval/README.md](eval/README.md).

Latest overall metrics:

| Metric | Fixed-size | Structure-aware |
|---|---:|---:|
| Recall@3 | 0.52 | 0.60 |
| Recall@5 | 0.56 | 0.72 |
| Recall@10 | 0.76 | 0.80 |
| MRR | 0.527762 | 0.578667 |
| Indexed chunks | 5,973 | 14,157 |

Structure-aware chunking performs better overall and on the five table questions; fixed-size performs better on the five materially paraphrased questions. The gold set is small and concentrated in three RBI documents, and exact local-PDF page alignment is not fully established. OCR word accuracy is unmeasured. See the evaluation documentation before interpreting these results.

## Tests

Run the automated test suite:

```bash
python -m pytest -q
```

The latest recorded validation passed 21 tests. The gold-set validator separately checks the 25-question structure, category counts, document IDs and page-range bounds; it does not prove semantic correctness of every gold page assignment.

## Known limitations and evidence status

- Table extraction and reconstruction can lose numeric fidelity or table-cell relationships. Verify high-impact numeric values against the original PDF.
- OCR accuracy has not been measured against a manually transcribed scanned-page reference.
- The 10-page manual extraction sample was text-native; visual verification of the flagged table/layout pages remains incomplete.
- The evaluation is retrieval-only, uses a small non-blind gold set, and is not evidence of production compliance coverage.
- The committed screenshots document the current submission state; see `evidence/PHASE4_EVIDENCE_STATUS.md` for the evidence inventory.