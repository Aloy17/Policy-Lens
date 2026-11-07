from pathlib import Path
from typing import Any
import os

import pymupdf
import pytesseract
from PIL import Image

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


def apply_ocr_to_pages(pdf_path: str | Path, pages: list[dict[str, Any]],
                       min_words: int = 20, language: str = "eng") -> list[dict[str, Any]]:
    """OCR pages with insufficient extracted text."""
    processed_pages = []
    for page in pages:
        page_data = page.copy()
        if page["word_count"] < min_words:
            page_data["text"] = ocr_page(pdf_path, page["page_number"], language)
            page_data["word_count"] = len(page_data["text"].split())
            page_data["has_text"] = bool(page_data["text"].strip())
            page_data["ocr_used"] = True
        else:
            page_data["ocr_used"] = False
        processed_pages.append(page_data)
    return processed_pages
