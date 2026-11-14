from pathlib import Path
from typing import Any

import pymupdf


def _native_table_rows(
    page: pymupdf.Page,
    table: Any,
    row_count: int,
    column_count: int,
) -> list[list[str]] | None:
    """Rebuild table cells from positioned native words and cell geometry.

    PyMuPDF's flat table.cells sequence is not guaranteed to be row-major.
    Derive row and column positions from each cell's coordinates instead.
    """
    cells = getattr(table, "cells", None)
    if not cells or len(cells) < row_count * column_count:
        return None

    valid_cells = [
        tuple(map(float, cell[:4]))
        for cell in cells
        if cell is not None and len(cell) >= 4
    ]
    if len(valid_cells) < row_count * column_count:
        return None

    row_positions = sorted({round(cell[1], 3) for cell in valid_cells})
    column_positions = sorted({round(cell[0], 3) for cell in valid_cells})
    if len(row_positions) != row_count or len(column_positions) != column_count:
        return None

    try:
        words = page.get_text("words")
    except Exception:
        return None

    rows = [["" for _ in range(column_count)] for _ in range(row_count)]
    assigned = 0
    for x0, y0, x1, y1 in valid_cells:
        row_index = min(range(row_count), key=lambda i: abs(row_positions[i] - y0))
        column_index = min(
            range(column_count), key=lambda i: abs(column_positions[i] - x0)
        )
        cell_words = []
        for word in words:
            wx0, wy0, wx1, wy1, word_text = word[:5]
            center_x = (float(wx0) + float(wx1)) / 2
            center_y = (float(wy0) + float(wy1)) / 2
            if x0 <= center_x <= x1 and y0 <= center_y <= y1:
                cell_words.append((float(wy0), float(wx0), str(word_text)))
        cell_words.sort(key=lambda item: (item[0], item[1]))
        if cell_words:
            rows[row_index][column_index] = " ".join(
                item[2] for item in cell_words
            )
            assigned += len(cell_words)

    return rows if assigned else None

def _merge_table_cell(extracted: str, positioned: str) -> str:
    """Combine table extraction and positioned words without corrupting decimals."""
    if not positioned:
        return extracted
    decimal_pattern = r"\d\s*[.,]\s*\d"
    extracted_has_decimal = re.search(decimal_pattern, extracted) is not None
    positioned_has_decimal = re.search(decimal_pattern, positioned) is not None
    if extracted_has_decimal and not positioned_has_decimal:
        return extracted
    if positioned_has_decimal and not extracted_has_decimal:
        return positioned
    if extracted_has_decimal and positioned_has_decimal:
        return extracted
    return positioned or extracted


def _extract_tables(page: pymupdf.Page) -> list[str]:
    """Extract tables while preferring source-positioned words for cell text."""
    if not hasattr(page, "find_tables"):
        return []

    try:
        finder = page.find_tables()
    except Exception as exc:
        raise RuntimeError("PyMuPDF table detection failed") from exc

    rendered = []
    for table_number, table in enumerate(finder.tables, start=1):
        try:
            extracted = table.extract() or []
        except Exception as exc:
            raise RuntimeError(
                f"PyMuPDF failed to extract table {table_number}"
            ) from exc
        rows = [
            ["" if cell is None else " ".join(str(cell).split()) for cell in row]
            for row in extracted
        ]
        if not rows:
            continue

        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        native_rows = _native_table_rows(page, table, len(rows), width)
        if native_rows is not None:
            rows = [
                [
                    _merge_table_cell(rows[r][c], native_rows[r][c])
                    for c in range(width)
                ]
                for r in range(len(rows))
            ]

        separator = ["---"] * width
        markdown_rows = [
            "| " + " | ".join(row) + " |"
            for row in [rows[0], separator, *rows[1:]]
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


def _extract_page_text(page: pymupdf.Page) -> str:
    """Extract page text in column order when a two-column layout is detected."""
    blocks = []
    for block in page.get_text("blocks"):
        if len(block) < 7 or not isinstance(block[4], str):
            continue
        text = block[4].strip()
        if text:
            blocks.append((float(block[0]), float(block[1]), float(block[2]),
                           float(block[3]), text))

    if not blocks:
        return page.get_text("text", sort=True)

    midpoint = page.rect.width / 2
    narrow = [b for b in blocks if (b[2] - b[0]) < page.rect.width * 0.65]
    left = [
        block for block in narrow
        if (block[0] + block[2]) / 2 < midpoint
    ]
    right = [
        block for block in narrow
        if (block[0] + block[2]) / 2 >= midpoint
    ]

    # Classify each block into exactly one column. A tolerance-based edge
    # check can place blocks in the center gutter into both columns.
    if len(left) < 2 or len(right) < 2 or len(narrow) < 4:
        return page.get_text("text", sort=True)

    spanning = [b for b in blocks if b not in narrow]
    column_top = min([b[1] for b in left + right])
    column_bottom = max([b[3] for b in left + right])
    top = sorted([b for b in spanning if b[1] <= column_top], key=lambda b: b[1])
    bottom = sorted([b for b in spanning if b[1] > column_bottom], key=lambda b: b[1])
    left = sorted(left, key=lambda b: (b[1], b[0]))
    right = sorted(right, key=lambda b: (b[1], b[0]))
    middle = sorted([b for b in spanning if b not in top and b not in bottom],
                    key=lambda b: (b[1], b[0]))
    ordered = top + left + middle + right + bottom
    return "\n".join(block[4] for block in ordered)


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
            text = _extract_page_text(page)
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
                    "table_text": "\n\n".join(tables),
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
