import re
from collections import Counter
from typing import Any


def normalize_whitespace(text: str) -> str:
    """Normalize spaces while preserving paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    cleaned_lines = []
    previous_blank = False

    for line in lines:
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
        else:
            cleaned_lines.append(line)
            previous_blank = False

    return "\n".join(cleaned_lines).strip()


def fix_hyphenation(text: str) -> str:
    """
    Join words that were split across lines by a hyphen.

    Example:
        disburse-
        ment

    becomes:
        disbursement
    """
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def remove_page_numbers(text: str) -> str:
    """Remove standalone page-number lines."""
    lines = text.split("\n")

    cleaned = []

    for line in lines:
        stripped = line.strip()

        if re.fullmatch(r"(page\s+)?\d+", stripped, flags=re.IGNORECASE):
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def find_repeated_lines(
    pages: list[dict[str, Any]],
    min_occurrences: int = 3,
) -> set[str]:
    """
    Find lines that repeat across multiple pages.

    These are candidates for repeated headers or footers.
    """
    counter = Counter()

    for page in pages:
        seen_on_page = set()

        for line in page["text"].splitlines():
            normalized = line.strip()

            if normalized:
                seen_on_page.add(normalized)

        for line in seen_on_page:
            counter[line] += 1

    return {
        line
        for line, count in counter.items()
        if count >= min_occurrences
    }


def clean_page_text(
    text: str,
    repeated_lines: set[str] | None = None,
) -> str:
    """Clean text from one PDF page."""
    text = fix_hyphenation(text)
    text = remove_page_numbers(text)

    if repeated_lines:
        lines = []

        for line in text.splitlines():
            if line.strip() not in repeated_lines:
                lines.append(line)

        text = "\n".join(lines)

    return normalize_whitespace(text)


def clean_pages(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Clean all parsed/OCR pages while preserving page metadata.
    """
    repeated_lines = find_repeated_lines(pages)

    cleaned_pages = []

    for page in pages:
        page_data = page.copy()

        original_text = page["text"]
        cleaned_text = clean_page_text(
            original_text,
            repeated_lines,
        )

        page_data["original_text"] = original_text
        page_data["text"] = cleaned_text
        page_data["original_word_count"] = len(original_text.split())
        page_data["word_count"] = len(cleaned_text.split())
        page_data["removed_word_count"] = (
            page_data["original_word_count"]
            - page_data["word_count"]
        )

        cleaned_pages.append(page_data)

    return cleaned_pages
