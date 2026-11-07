# PolicyLens

PolicyLens is a PDF ingestion and retrieval system for regulatory circulars and policy documents. It extracts text, applies OCR fallback, creates fixed-size and structure-aware chunks, indexes them in ChromaDB, and provides a Streamlit retrieval interface.

## Standalone macOS application (Apple Silicon)

A portable ARM64 macOS build is documented in [packaging/README.md](packaging/README.md). It bundles Python dependencies, Tesseract OCR and the embedding model. The generated `dist/PolicyLens/` folder contains `PolicyLens.app` and a sibling `PolicyLens Data/` folder. Keep them together; delete the complete distribution folder to remove application-managed files. macOS may retain generic system metadata outside it.

## Development installation

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

On macOS, install Tesseract with `brew install tesseract`. On Ubuntu/Debian use
`sudo apt install tesseract-ocr`. On Windows, install Tesseract and add it to PATH.

## Corpus and indexing

The source PDFs and `data/manifest.csv` are required. Build the vector index:

```bash
python ingest.py --input data/pdfs --manifest data/manifest.csv --collection policylens_v1
```

The first run downloads the configured Sentence Transformer model unless a
local model path is configured. ChromaDB data and logs are stored locally.

## Search

```bash
PYTHONPATH=. python search.py "What are the KYC requirements for regulated entities?"
streamlit run ui/app.py
```

CLI options include `--top_k N`, `--strategy fixed|structure`, and repeated
`--filter KEY=VALUE` arguments.

## Tests

```bash
python -m pytest -q
```

The project compares fixed-size and structure-aware retrieval using Recall@K
and MRR. Table-value retrieval remains a known limitation.
