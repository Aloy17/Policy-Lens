import re
from typing import Any


def tokenize(text: str) -> list[str]:
    """Split text into simple whitespace-based tokens."""
    return text.split()


def detokenize(tokens: list[str]) -> str:
    """Convert tokens back into text."""
    return " ".join(tokens)


def create_chunk(
    text: str,
    page_start: int,
    page_end: int,
    section_title: str = "",
    ocr_used: bool = False,
) -> dict[str, Any]:
    """Create a standardized chunk dictionary."""
    return {
        "text": text.strip(),
        "page_start": page_start,
        "page_end": page_end,
        "section_title": section_title,
        "token_count": len(tokenize(text)),
        "ocr_used": ocr_used,
    }


def fixed_size_chunks(
    pages: list[dict[str, Any]],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """Create fixed-size chunks with token overlap."""
    chunks = []

    all_tokens: list[tuple[str, int]] = []

    for page in pages:
        for token in tokenize(page["text"]):
            all_tokens.append(
                (token, page["page_number"])
            )

    if not all_tokens:
        return chunks

    step = max(1, chunk_size - overlap)

    for start in range(0, len(all_tokens), step):
        end = min(start + chunk_size, len(all_tokens))
        chunk_items = all_tokens[start:end]

        if not chunk_items:
            break

        tokens = [item[0] for item in chunk_items]
        page_numbers = [item[1] for item in chunk_items]

        ocr_used = any(
            pages[page_number - 1].get("ocr_used", False)
            for page_number in set(page_numbers)
        )

        chunks.append(
            create_chunk(
                text=detokenize(tokens),
                page_start=min(page_numbers),
                page_end=max(page_numbers),
                ocr_used=ocr_used,
            )
        )

        if end >= len(all_tokens):
            break

    return chunks


def looks_like_heading(line: str) -> bool:
    """
    Detect likely structural headings without treating
    numbered regulatory clauses as headings.
    """
    stripped = line.strip()

    if not stripped:
        return False

    if len(stripped) > 120:
        return False

    # Major document structures.
    if re.match(
        r"^(chapter|part|section|annex|appendix|schedule)"
        r"\s+[A-Za-z0-9IVXLC\-]+",
        stripped,
        re.IGNORECASE,
    ):
        return True

    # Common heading-style text.
    if stripped.isupper() and 1 <= len(stripped.split()) <= 12:
        return True

    return False


def split_into_sections(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Split the document into meaningful structural sections."""
    sections = []

    current_lines: list[str] = []
    current_pages: list[int] = []
    current_heading = ""
    current_ocr_used = False

    for page in pages:
        page_number = page["page_number"]
        page_ocr_used = page.get("ocr_used", False)

        for line in page["text"].splitlines():
            line = line.strip()

            if not line:
                continue

            if looks_like_heading(line):
                if current_lines:
                    sections.append(
                        {
                            "text": "\n".join(current_lines),
                            "page_start": min(current_pages),
                            "page_end": max(current_pages),
                            "section_title": current_heading,
                            "ocr_used": current_ocr_used,
                        }
                    )

                current_lines = [line]
                current_pages = [page_number]
                current_heading = line
                current_ocr_used = page_ocr_used

            else:
                current_lines.append(line)
                current_pages.append(page_number)
                current_ocr_used = (
                    current_ocr_used or page_ocr_used
                )

    if current_lines:
        sections.append(
            {
                "text": "\n".join(current_lines),
                "page_start": min(current_pages),
                "page_end": max(current_pages),
                "section_title": current_heading,
                "ocr_used": current_ocr_used,
            }
        )

    return sections


def merge_small_sections(
    sections: list[dict[str, Any]],
    min_size: int,
    max_size: int,
) -> list[dict[str, Any]]:
    """
    Merge small neighboring sections so that short headings
    and clauses do not become tiny chunks.
    """
    if not sections:
        return []

    merged = []

    for section in sections:
        section_tokens = tokenize(section["text"])

        if not merged:
            merged.append(section.copy())
            continue

        previous = merged[-1]
        previous_tokens = tokenize(previous["text"])

        combined_size = len(previous_tokens) + len(section_tokens)

        if len(section_tokens) < min_size and combined_size <= max_size:
            previous["text"] = (
                previous["text"] + "\n" + section["text"]
            )
            previous["page_end"] = section["page_end"]

            previous["ocr_used"] = (
                previous.get("ocr_used", False)
                or section.get("ocr_used", False)
            )

        else:
            merged.append(section.copy())

    return merged


def split_large_section(
    section: dict[str, Any],
    target_size: int = 500,
    max_size: int = 800,
    min_size: int = 300,
) -> list[dict[str, Any]]:
    """Split large sections while keeping chunks within the target range."""
    tokens = tokenize(section["text"])

    if len(tokens) <= max_size:
        return [
            create_chunk(
                text=section["text"],
                page_start=section["page_start"],
                page_end=section["page_end"],
                section_title=section["section_title"],
                ocr_used=section.get("ocr_used", False),
            )
        ]

    chunks = []

    for start in range(0, len(tokens), target_size):
        end = min(start + target_size, len(tokens))
        chunk_tokens = tokens[start:end]

        if len(chunk_tokens) < min_size and chunks:
            previous = chunks[-1]
            previous_tokens = tokenize(previous["text"])

            if len(previous_tokens) + len(chunk_tokens) <= max_size:
                previous["text"] = detokenize(
                    previous_tokens + chunk_tokens
                )
                previous["token_count"] = len(
                    tokenize(previous["text"])
                )
                continue

        chunks.append(
            create_chunk(
                text=detokenize(chunk_tokens),
                page_start=section["page_start"],
                page_end=section["page_end"],
                section_title=section["section_title"],
                ocr_used=section.get("ocr_used", False),
            )
        )

    return chunks


def structure_aware_chunks(
    pages: list[dict[str, Any]],
    target_size: int = 500,
    max_size: int = 800,
    min_size: int = 300,
) -> list[dict[str, Any]]:
    """
    Create structure-aware chunks based on meaningful headings,
    then merge small sections and split large sections.
    """
    sections = split_into_sections(pages)

    sections = merge_small_sections(
        sections,
        min_size=min_size,
        max_size=max_size,
    )

    chunks = []

    for section in sections:
        chunks.extend(
            split_large_section(
                section,
                target_size=target_size,
                max_size=max_size,
                min_size=min_size,
            )
        )

    return chunks