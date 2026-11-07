import re
from typing import Any, Callable


def tokenize(text: str) -> list[str]:
    """Fallback whitespace tokenizer; production ingestion supplies model tokenizer."""
    return text.split()


def detokenize(tokens: list[str]) -> str:
    return " ".join(tokens)


def _encode(text: str, tokenizer: Any = None) -> list[int] | list[str]:
    if tokenizer is None:
        return tokenize(text)
    return tokenizer.encode(text, add_special_tokens=False)


def _decode(tokens: list[int] | list[str], tokenizer: Any = None) -> str:
    if tokenizer is None:
        return detokenize(tokens)
    return tokenizer.decode(tokens, skip_special_tokens=True).strip()


def _token_count(text: str, tokenizer: Any = None) -> int:
    return len(_encode(text, tokenizer))


def create_chunk(text: str, page_start: int, page_end: int,
                 section_title: str = "", ocr_used: bool = False,
                 tokenizer: Any = None) -> dict[str, Any]:
    """Create a standardized chunk dictionary with model-token count."""
    return {
        "text": text.strip(),
        "page_start": page_start,
        "page_end": page_end,
        "section_title": section_title,
        "token_count": _token_count(text, tokenizer),
        "ocr_used": ocr_used,
    }


def _page_token_stream(pages: list[dict[str, Any]], tokenizer: Any = None):
    stream = []
    for page in pages:
        ids = _encode(page["text"], tokenizer)
        stream.extend((token, page["page_number"], page.get("ocr_used", False)) for token in ids)
    return stream


def fixed_size_chunks(pages: list[dict[str, Any]], chunk_size: int = 500,
                      overlap: int = 50, tokenizer: Any = None) -> list[dict[str, Any]]:
    """Create fixed-size chunks using the embedding model tokenizer."""
    stream = _page_token_stream(pages, tokenizer)
    chunks = []
    if not stream:
        return chunks
    step = max(1, chunk_size - overlap)
    for start in range(0, len(stream), step):
        items = stream[start:start + chunk_size]
        if not items:
            break
        text = _decode([item[0] for item in items], tokenizer)
        page_numbers = [item[1] for item in items]
        chunks.append(create_chunk(
            text, min(page_numbers), max(page_numbers),
            ocr_used=any(item[2] for item in items), tokenizer=tokenizer))
        if start + chunk_size >= len(stream):
            break
    return chunks


def looks_like_heading(line: str) -> bool:
    """Detect major headings and short uppercase headings."""
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False
    if re.match(r"^(chapter|part|section|annex|appendix|schedule)\s+[A-Za-z0-9IVXLC\-]+",
                stripped, re.IGNORECASE):
        return True
    return stripped.isupper() and 1 <= len(stripped.split()) <= 12


def structure_aware_chunks(pages: list[dict[str, Any]], target_size: int = 500,
                           max_size: int = 800, min_size: int = 300,
                           tokenizer: Any = None) -> list[dict[str, Any]]:
    """
    Split on detected headings, then token-budget paragraphs while retaining
    the page number of every token. Table rows remain in their source order.
    """
    sections = []
    current_title = ""
    current_lines = []
    for page in pages:
        for line in page["text"].splitlines():
            line = line.strip()
            if not line:
                continue
            if looks_like_heading(line):
                if current_lines:
                    sections.append(current_lines)
                current_title = line
                current_lines = []
            current_lines.append((line, page["page_number"], page.get("ocr_used", False), current_title))
    if current_lines:
        sections.append(current_lines)

    chunks = []
    for section in sections:
        buffer_ids = []
        buffer_pages = []
        buffer_ocr = []
        title = section[0][3] if section else ""
        for line, page_number, ocr_used, line_title in section:
            line_ids = _encode(line, tokenizer)
            # A single long line/table row is split rather than exceeding max_size.
            while line_ids:
                remaining = max_size - len(buffer_ids)
                if remaining <= 0:
                    chunks.append(create_chunk(_decode(buffer_ids, tokenizer),
                        min(buffer_pages), max(buffer_pages), title,
                        any(buffer_ocr), tokenizer))
                    buffer_ids, buffer_pages, buffer_ocr = [], [], []
                    remaining = max_size
                take = min(len(line_ids), remaining)
                buffer_ids.extend(line_ids[:take])
                buffer_pages.extend([page_number] * take)
                buffer_ocr.extend([ocr_used] * take)
                line_ids = line_ids[take:]
                if len(buffer_ids) >= target_size and len(buffer_ids) >= min_size:
                    chunks.append(create_chunk(_decode(buffer_ids, tokenizer),
                        min(buffer_pages), max(buffer_pages), title,
                        any(buffer_ocr), tokenizer))
                    buffer_ids, buffer_pages, buffer_ocr = [], [], []
        if buffer_ids:
            if chunks and len(buffer_ids) < min_size:
                previous = chunks[-1]
                combined = previous["text"] + " " + _decode(buffer_ids, tokenizer)
                if _token_count(combined, tokenizer) <= max_size:
                    previous["text"] = combined
                    previous["page_end"] = max(previous["page_end"], max(buffer_pages))
                    previous["token_count"] = _token_count(combined, tokenizer)
                    previous["ocr_used"] = previous["ocr_used"] or any(buffer_ocr)
                    continue
            chunks.append(create_chunk(_decode(buffer_ids, tokenizer),
                min(buffer_pages), max(buffer_pages), title,
                any(buffer_ocr), tokenizer))

    return chunks
