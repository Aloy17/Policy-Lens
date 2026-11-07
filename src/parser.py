from pathlib import Path
from typing import Any

import pymupdf


def _extract_tables(page: pymupdf.Page) -> list[str]:
    """Extract detected tables as readable Markdown-like text."""
    if not hasattr(page, "find_tables"):
        return []

    try:
        finder = page.find_tables()
    except Exception:
        return []

    rendered = []
    for table_number, table in enumerate(finder.tables, start=1):
        rows = table.extract() or []
        rows = [
            ["" if cell is None else " ".join(str(cell).split()) for cell in row]
            for row in rows
        ]
        if not rows:
            continue

        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        header = rows[0]
        separator = ["---"] * width
        markdown_rows = [
            "| " + " | ".join(row) + " |"
            for row in [header, separator, *rows[1:]]
        ]
        rendered.append(f"[TABLE {table_number}]\n" + "\n".join(markdown_rows))

    return rendered


def _image_coverage(page: pymupdf.Page) -> float:
    """Estimate the proportion of a page covered by raster images."""
    page_area = page.rect.width * page.rect.height
    if page_area <= 0:
        return 0.0

    image_area = 0.0
    try:
        for image in page.get_image_info():
            x0, y0, x1, y1 = image["bbox"]
            image_area += max(0.0, x1 - x0) * max(0.0, y1 - y0)
    except Exception:
        return 0.0

    return min(1.0, image_area / page_area)


def parse_pdf(pdf_path: str | Path) -> list[dict[str, Any]]:
    """
    Extract page-level text and detected tables while preserving page numbers.

    Text extraction uses PyMuPDF's sorted reading order. Table extraction is
    additive: the original page text remains available alongside table rows.
    """
    pdf_path = Path(pdf_path)
    pages = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True)
            tables = _extract_tables(page)
            if tables:
                text = text.rstrip() + "\n\n" + "\n\n".join(tables)

            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "word_count": len(text.split()),
                    "has_text": bool(text.strip()),
                    "table_count": len(tables),
                    "image_coverage": _image_coverage(page),
                }
            )

    return pages


def get_page_count(pdf_path: str | Path) -> int:
    """Return the total number of pages in a PDF."""
    with pymupdf.open(Path(pdf_path)) as document:
        return len(document)


def detect_scanned_pages(
    pages: list[dict[str, Any]],
    min_words: int = 20,
    image_coverage_threshold: float = 0.5,
    image_text_word_limit: int = 120,
) -> list[int]:
    """
    Identify pages that need OCR based on sparse text or image-dominant layout.

    The second condition catches scanned pages that contain a poor embedded
    OCR layer and would otherwise pass a simple minimum-word threshold.
    """
    return [
        page["page_number"]
        for page in pages
        if page["word_count"] < min_words
        or (
            page.get("image_coverage", 0.0) >= image_coverage_threshold
            and page["word_count"] < image_text_word_limit
        )
    ]
