from pathlib import Path
from typing import Any
import os

import pymupdf
import pytesseract
from PIL import Image

from src.parser import detect_scanned_pages

_tesseract_cmd = os.environ.get("POLICYLENS_TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd


def ocr_page(pdf_path: str | Path, page_number: int, language: str = "eng") -> str:
    """Run OCR on one 1-based PDF page."""
    with pymupdf.open(Path(pdf_path)) as document:
        page = document[page_number - 1]
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        return pytesseract.image_to_string(image, lang=language)


def apply_ocr_to_pages(
    pdf_path: str | Path,
    pages: list[dict[str, Any]],
    min_words: int = 20,
    language: str = "eng",
    enabled: bool = True,
    image_coverage_threshold: float = 0.5,
    image_text_word_limit: int = 120,
) -> list[dict[str, Any]]:
    """OCR pages flagged by text density or image coverage when OCR is enabled."""
    processed_pages = []
    ocr_page_numbers = set(
        detect_scanned_pages(
            pages,
            min_words=min_words,
            image_coverage_threshold=image_coverage_threshold,
            image_text_word_limit=image_text_word_limit,
        )
    ) if enabled else set()

    for page in pages:
        page_data = page.copy()
        if page["page_number"] in ocr_page_numbers:
            ocr_text = ocr_page(pdf_path, page["page_number"], language)
            if ocr_text.strip():
                table_text = page.get("table_text", "")
                page_data["text"] = ocr_text.rstrip()
                if table_text:
                    page_data["text"] += "\n\n" + table_text
                page_data["word_count"] = len(page_data["text"].split())
                page_data["has_text"] = True
            page_data["ocr_used"] = True
        else:
            page_data["ocr_used"] = False
        processed_pages.append(page_data)

    return processed_pages
