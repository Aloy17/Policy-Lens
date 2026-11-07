from pathlib import Path
from typing import Any

import pymupdf


def parse_pdf(pdf_path: str | Path) -> list[dict[str, Any]]:
    """
    Extract text from a PDF while preserving page numbers.

    Returns one dictionary per page.
    """
    pdf_path = Path(pdf_path)
    pages = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")

            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "word_count": len(text.split()),
                    "has_text": bool(text.strip()),
                }
            )

    return pages


def get_page_count(pdf_path: str | Path) -> int:
    """Return the total number of pages in a PDF."""
    pdf_path = Path(pdf_path)

    with pymupdf.open(pdf_path) as document:
        return len(document)


def detect_scanned_pages(
    pages: list[dict[str, Any]],
    min_words: int = 20,
) -> list[int]:
    """
    Identify pages that probably need OCR.

    A page is considered a possible scanned page when its
    extracted text contains fewer than min_words words.
    """
    return [
        page["page_number"]
        for page in pages
        if page["word_count"] < min_words
    ]
