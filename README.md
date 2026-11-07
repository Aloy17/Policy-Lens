# PolicyLens

PolicyLens is a PDF ingestion and retrieval system for regulatory circulars and policy documents. It processes PDF files, extracts text, applies OCR fallback to scanned pages, creates chunks and indexes them in ChromaDB for semantic search.

The project compares two retrieval approaches:
- Fixed-size chunking
- Structure-aware chunking

The application retrieves relevant passages with document names, page numbers and section information. It focuses on retrieval rather than generating answers with an LLM.

## Features

- PDF text extraction using PyMuPDF
- OCR fallback using Tesseract
- Text cleaning and chunking
- Fixed-size and structure-aware chunking strategies
- Sentence Transformer embeddings
- Persistent ChromaDB vector storage
- Idempotent ingestion
- Source and page-level retrieval metadata
- Streamlit search interface
- Retrieval evaluation using Recall@K and MRR

## Requirements

- Python 3.10 or newer
- Tesseract OCR
- Git

## Installation

Clone the repository:

```bash
git clone https://github.com/mathur458/PolicyLens.git
cd PolicyLens
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-ui.txt
```

## Install Tesseract OCR

On macOS with Homebrew:

```bash
brew install tesseract
```

On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

On Windows, install Tesseract OCR and ensure its installation directory is added to PATH.

Check the installation:

```bash
tesseract --version
```

## Prepare the corpus

The repository includes the source PDFs and `data/manifest.csv`.

The manifest contains document metadata such as:
- Document ID
- Title
- Issuer
- Issue date
- Source URL
- Page count
- Document type

Make sure the PDF files are present in `data/pdfs/` before running ingestion.

## Build the vector database

The ChromaDB database is intentionally excluded from GitHub because it is generated locally and can be recreated from the source PDFs.

Run:

```bash
python ingest.py --input data/pdfs --manifest data/manifest.csv --collection policylens_v1
```

This creates the local ChromaDB collections used by the application.

Ingestion may take some time depending on the machine and corpus size. The first run also downloads the embedding model if it is not already available.

## Run the search interface

Start the Streamlit application:

```bash
streamlit run ui/app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## Search from the command line

Example:

```bash
PYTHONPATH=. python search.py "What are the KYC requirements for regulated entities?"
```

## Run evaluation

```bash
PYTHONPATH=. python eval/evaluate.py
```

The evaluation compares fixed-size and structure-aware retrieval using:
- Recall@3
- Recall@5
- Recall@10
- Mean Reciprocal Rank (MRR)

The evaluation questions and retrieval results are stored in the `eval/` directory.

## Run automated tests

```bash
python -m pytest -q
```

## Project structure

```text
PolicyLens/
├── data/
│   ├── pdfs/
│   ├── manifest.csv
│   ├── build_corpus.py
│   └── download_corpus.py
├── eval/
│   ├── questions.csv
│   ├── evaluate.py
│   └── retrieval_log_final.csv
├── logs/
├── report/
├── src/
│   ├── parser.py
│   ├── ocr.py
│   ├── cleaner.py
│   ├── chunker.py
│   ├── metadata.py
│   ├── embedder.py
│   └── vector_store.py
├── tests/
├── ui/
│   └── app.py
├── ingest.py
├── search.py
├── config.yaml
├── requirements.txt
└── requirements-ui.txt
```

## Important notes

- `chroma_db/` is local generated data and is not committed to GitHub.
- Every user must run ingestion locally after cloning before using search.
- The source PDFs and manifest are required to rebuild the database.
- The embedding model is downloaded locally when first required.
- No API key is required for the configured local embedding model.
- OCR requires a working Tesseract installation.

## Evaluation observations

Structure-aware chunking performed better overall on the evaluation questions. However, table-value retrieval remains a limitation and requires further improvement.

The evaluation uses 25 questions, including paraphrased and table-related questions. Results are available in the `eval/` directory.

## Report

The technical report documents the architecture, corpus, implementation, evaluation results, limitations and recommendations.
