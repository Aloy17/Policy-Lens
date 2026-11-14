import re
from typing import Any


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


def _is_table_separator(line: str) -> bool:
    """Return True only for a Markdown table separator row."""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    cells = stripped.strip("|").split("|")
    return bool(cells) and all(
        re.fullmatch(r"\s*:?-{3,}:?\s*", cell) is not None
        for cell in cells
    )


def _split_text_with_prefix(
    text: str,
    prefix_text: str,
    max_size: int,
    tokenizer: Any = None,
) -> list[str]:
    """Split text into loss-minimizing token fragments under a repeated prefix."""
    token_ids = _encode(text, tokenizer)
    if not token_ids:
        return []

    if _token_count(prefix_text, tokenizer) >= max_size:
        raise ValueError("Table context leaves no room for content")

    fragments = []
    offset = 0
    while offset < len(token_ids):
        low = 1
        high = len(token_ids) - offset
        best_end = offset
        best_text = ""

        while low <= high:
            middle = (low + high) // 2
            fragment = _decode(token_ids[offset:offset + middle], tokenizer)
            candidate = prefix_text + "\n" + fragment if prefix_text else fragment
            if _token_count(candidate, tokenizer) <= max_size:
                best_end = offset + middle
                best_text = fragment
                low = middle + 1
            else:
                high = middle - 1

        if best_end == offset:
            raise ValueError("Unable to fit table content within the maximum chunk size")

        fragments.append(best_text)
        offset = best_end

    return fragments


def _table_chunks(
    table_lines: list[tuple[str, int, bool]],
    section_title: str,
    max_size: int,
    tokenizer: Any = None,
) -> list[dict[str, Any]]:
    """Chunk a Markdown table, preserving oversized first rows as continuations."""
    if len(table_lines) < 2:
        return [
            create_chunk(line, page, page, section_title, ocr, tokenizer)
            for line, page, ocr in table_lines
        ]

    marker = table_lines[0]
    first_row = table_lines[1]
    separator = (
        table_lines[2]
        if len(table_lines) > 2 and _is_table_separator(table_lines[2][0])
        else None
    )
    body_start = 3 if separator else 2

    marker_text = marker[0]
    first_row_prefix = marker_text + "\n" + first_row[0]
    first_row_is_oversized = _token_count(first_row_prefix, tokenizer) >= max_size

    chunks = []

    if first_row_is_oversized:
        # The first extracted row may itself be very long. Preserve it in
        # bounded continuation chunks instead of treating it as mandatory
        # repeated context for every subsequent row.
        continuation_prefix = marker_text + "\n[FIRST ROW CONTINUATION]"
        fragments = _split_text_with_prefix(
            first_row[0], continuation_prefix, max_size, tokenizer
        )
        for fragment in fragments:
            chunks.append(create_chunk(
                continuation_prefix + "\n" + fragment,
                first_row[1],
                first_row[1],
                section_title,
                marker[2] or first_row[2],
                tokenizer,
            ))
        prefix_lines = [marker]
        prefix_text = (
            marker_text
            + "\n[FIRST ROW EXCEEDS CHUNK LIMIT; SEE FIRST ROW CONTINUATION]"
        )
    else:
        prefix_lines = [marker, first_row]
        prefix_text = first_row_prefix

        # A Markdown separator is presentation-only. Keep it only when it
        # fits alongside the substantive first row.
        if separator:
            candidate = prefix_text + "\n" + separator[0]
            if _token_count(candidate, tokenizer) < max_size:
                prefix_lines.append(separator)
                prefix_text = candidate

    prefix_tokens = _encode(prefix_text, tokenizer)
    if len(prefix_tokens) >= max_size:
        raise ValueError("Table context exceeds the maximum chunk size")

    body_buffer: list[tuple[str, int, bool]] = []

    def emit(rows: list[tuple[str, int, bool]]) -> None:
        if not rows:
            return
        text = prefix_text + "\n" + "\n".join(item[0] for item in rows)
        page_numbers = [item[1] for item in prefix_lines + rows]
        chunks.append(create_chunk(
            text,
            min(page_numbers),
            max(page_numbers),
            section_title,
            any(item[2] for item in prefix_lines + rows),
            tokenizer,
        ))

    for row in table_lines[body_start:]:
        candidate = body_buffer + [row]
        candidate_text = prefix_text + "\n" + "\n".join(item[0] for item in candidate)
        if _token_count(candidate_text, tokenizer) <= max_size:
            body_buffer.append(row)
            continue

        if body_buffer:
            emit(body_buffer)
            body_buffer = []

        single_text = prefix_text + "\n" + row[0]
        if _token_count(single_text, tokenizer) <= max_size:
            body_buffer = [row]
            continue

        row_prefix = prefix_text
        fragments = _split_text_with_prefix(row[0], row_prefix, max_size, tokenizer)
        for fragment in fragments:
            chunks.append(create_chunk(
                row_prefix + "\n" + fragment,
                min(item[1] for item in prefix_lines + [row]),
                max(item[1] for item in prefix_lines + [row]),
                section_title,
                any(item[2] for item in prefix_lines) or row[2],
                tokenizer,
            ))

    emit(body_buffer)
    if not chunks:
        chunks.append(create_chunk(
            prefix_text,
            marker[1],
            max(item[1] for item in prefix_lines),
            section_title,
            any(item[2] for item in prefix_lines),
            tokenizer,
        ))
    return chunks


def structure_aware_chunks(pages: list[dict[str, Any]], target_size: int = 500,
                           max_size: int = 800, min_size: int = 300,
                           tokenizer: Any = None) -> list[dict[str, Any]]:
    """
    Split on headings and preserve table context across chunk boundaries.

    Table continuations repeat their table marker, column header, and separator.
    Complete body rows stay together unless an individual row exceeds the
    configured maximum token budget.
    """
    segments = []
    current_title = ""
    current_lines = []
    for page in pages:
        lines = page["text"].splitlines()
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if not line:
                index += 1
                continue
            if line.startswith("[TABLE "):
                if current_lines:
                    segments.append(("text", current_lines, current_title))
                    current_lines = []
                table_lines = [(line, page["page_number"], page.get("ocr_used", False))]
                index += 1
                while index < len(lines):
                    candidate = lines[index].strip()
                    if not candidate:
                        index += 1
                        continue
                    if not candidate.startswith("|"):
                        break
                    table_lines.append((candidate, page["page_number"], page.get("ocr_used", False)))
                    index += 1
                segments.append(("table", table_lines, current_title))
                continue
            if looks_like_heading(line):
                if current_lines:
                    segments.append(("text", current_lines, current_title))
                    current_lines = []
                current_title = line
            current_lines.append((line, page["page_number"], page.get("ocr_used", False), current_title))
            index += 1

    if current_lines:
        segments.append(("text", current_lines, current_title))

    chunks = []
    for segment_type, segment, title in segments:
        if segment_type == "table":
            chunks.extend(_table_chunks(segment, title, max_size, tokenizer))
            continue

        buffer_ids = []
        buffer_pages = []
        buffer_ocr = []
        section_title = segment[0][3] if segment else title
        for line, page_number, ocr_used, line_title in segment:
            line_ids = _encode(line, tokenizer)
            while line_ids:
                remaining = max_size - len(buffer_ids)
                if remaining <= 0:
                    chunks.append(create_chunk(_decode(buffer_ids, tokenizer),
                        min(buffer_pages), max(buffer_pages), section_title,
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
                        min(buffer_pages), max(buffer_pages), section_title,
                        any(buffer_ocr), tokenizer))
                    buffer_ids, buffer_pages, buffer_ocr = [], [], []
        if buffer_ids:
            if (chunks and len(buffer_ids) < min_size
                    and chunks[-1]["section_title"] == section_title
                    and "[TABLE " not in chunks[-1]["text"]):
                previous = chunks[-1]
                combined = previous["text"] + " " + _decode(buffer_ids, tokenizer)
                if _token_count(combined, tokenizer) <= max_size:
                    previous["text"] = combined
                    previous["page_end"] = max(previous["page_end"], max(buffer_pages))
                    previous["token_count"] = _token_count(combined, tokenizer)
                    previous["ocr_used"] = previous["ocr_used"] or any(buffer_ocr)
                    continue
            chunks.append(create_chunk(_decode(buffer_ids, tokenizer),
                min(buffer_pages), max(buffer_pages), section_title,
                any(buffer_ocr), tokenizer))

    return chunks
