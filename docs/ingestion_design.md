# PolicyLens ingestion design decisions

## PDF parsing and layout

PyMuPDF is used for page-level extraction because it exposes page text, block geometry, image coverage, page rendering and table detection through one local library. Text-native pages are extracted in sorted reading order. Pages with separate left/right text blocks are read column-by-column to avoid interleaving two-column prose. Detected tables are additionally extracted with PyMuPDF's table finder and serialized as Markdown-like rows so their cell relationships remain readable in retrieval chunks.

Table detection is heuristic and depends on visible cell boundaries/layout. Complex borderless tables and scanned tables may not be reconstructed perfectly; those cases must be checked in the manual page-quality sample. Original page text is retained alongside extracted table text.

## OCR fallback

Tesseract OCR is used locally through pytesseract. Pages are rendered at 2x scale before OCR. OCR is configurable and enabled by default.

A page is sent to OCR when either:
- its extracted text has fewer than 20 words; or
- raster images cover at least 50% of the page and the extracted text has fewer than 400 words.

The first condition catches image-only scans. The second catches pages with a weak embedded OCR layer. These are triage thresholds, not proof of OCR quality; representative scanned/mixed pages must be manually checked and OCR word accuracy estimated for the evaluation report. The configured OCR language is English (eng).

## Cleaning

Whitespace is normalized while paragraph breaks are retained. Line-break hyphenation is joined. Standalone page-number lines are removed. Repeated headers/footers are detected only among the first and last three lines of pages and removed only when they recur on at least three pages. Original page text and before/after word counts are retained for audit evidence.

## Chunking

Both strategies use the selected embedding model's tokenizer rather than whitespace word counts.

- Fixed-size: 500 model tokens with 50-token overlap.
- Structure-aware: heading-led sections, a 400-token target, 300-token minimum where merging is possible, and a 500-token maximum. Page attribution is tracked at token level; a chunk's page range reflects the pages contributing its text.

The model sentence-transformers/multi-qa-MiniLM-L6-cos-v1 has a 512-token input context. The 500-token chunk maximum leaves room for model-added special tokens and avoids silently truncating 800-token chunks. Short source sections may remain below 300 tokens when merging would cross the 500-token maximum or when the document itself is shorter; this is preferable to deleting content or combining unrelated sections.

## Metadata and source versioning

Every chunk carries doc_id, title, issuer, issue_date, page_start, page_end, section_title and SHA-256 source_hash. Strategy, OCR-use and document-type fields are also retained.

Chunk IDs include a prefix of the source hash. A changed source is parsed and embedded before stale chunks are deleted. The old version remains searchable if parsing, embedding or either index write fails. An unchanged document is skipped only when both strategy collections contain exactly that source version. A successful rerun removes stale versions after both replacement indexes have accepted the new chunks.

## Embeddings

The local Sentence Transformers model is sentence-transformers/multi-qa-MiniLM-L6-cos-v1. Its embedding dimension is 384. Embeddings are L2-normalized, and texts are encoded in batches of 32. Because embeddings are generated locally rather than through a metered hosted API, the external API cost is ₹0 / $0 per 1,000 chunks. Local compute time and electricity are hardware-dependent and will be measured during corpus ingestion rather than guessed. Transient local encoding failures are retried up to three times with exponential backoff. Hosted API rate limits do not apply to this local embedding path.

## Vector index

ChromaDB persistent collections are used for the fixed-size and structure-aware strategies. HNSW uses cosine distance. Normalized vectors are compatible with cosine similarity; the CLI's displayed score is 1 - cosine_distance. Chroma's HNSW settings other than the cosine space use library defaults; index size and query latency are measured during evaluation.
