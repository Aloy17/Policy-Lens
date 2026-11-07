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
    """Join words split across lines by a line-break hyphen."""
    return re.sub(r"(?<=[A-Za-z])-[ \t]*\n[ \t]*(?=[A-Za-z])", "", text)


def remove_page_numbers(text: str) -> str:
    """Remove standalone page-number lines."""
    return "\n".join(
        line for line in text.split("\n")
        if not re.fullmatch(r"(page\s+)?\d+", line.strip(), flags=re.IGNORECASE)
    )


def find_repeated_lines(pages: list[dict[str, Any]], min_occurrences: int = 3) -> set[str]:
    """Find repeated candidates only in the top/bottom three lines of pages."""
    counter = Counter()
    for page in pages:
        lines = page["text"].splitlines()
        edge_lines = lines[:3] + lines[-3:]
        for line in set(item.strip() for item in edge_lines if item.strip()):
            counter[line] += 1
    return {line for line, count in counter.items() if count >= min_occurrences}


def clean_page_text(text: str, repeated_lines: set[str] | None = None) -> str:
    """Clean page text without removing repeated lines from the body."""
    text = fix_hyphenation(text)
    lines = text.splitlines()
    if repeated_lines:
        for index in sorted(set(list(range(min(3, len(lines))) +
                                     list(range(max(0, len(lines)-3), len(lines))))),
                            reverse=True):
            if lines[index].strip() in repeated_lines:
                lines.pop(index)
    text = remove_page_numbers("\n".join(lines))
    return normalize_whitespace(text)


def clean_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Clean all pages while preserving original text for before/after evidence."""
    repeated_lines = find_repeated_lines(pages)
    cleaned_pages = []
    for page in pages:
        page_data = page.copy()
        original_text = page["text"]
        cleaned_text = clean_page_text(original_text, repeated_lines)
        page_data["original_text"] = original_text
        page_data["text"] = cleaned_text
        page_data["original_word_count"] = len(original_text.split())
        page_data["word_count"] = len(cleaned_text.split())
        page_data["removed_word_count"] = page_data["original_word_count"] - page_data["word_count"]
        cleaned_pages.append(page_data)
    return cleaned_pages
