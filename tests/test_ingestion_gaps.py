from src.chunker import fixed_size_chunks, structure_aware_chunks
from src.cleaner import clean_page_text, find_repeated_lines
from src.ocr import apply_ocr_to_pages
from src.parser import detect_scanned_pages


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))

    def decode(self, token_ids, skip_special_tokens=True):
        return " ".join("token" for _ in token_ids)


def test_model_tokenizer_controls_fixed_chunk_size():
    tokenizer = FakeTokenizer()
    pages = [{"page_number": 1, "text": "word " * 1100, "ocr_used": False}]
    chunks = fixed_size_chunks(pages, chunk_size=400, overlap=40, tokenizer=tokenizer)
    assert len(chunks) > 1
    assert all(chunk["token_count"] <= 400 for chunk in chunks)


def test_structure_chunks_keep_precise_page_ranges_and_token_limit():
    tokenizer = FakeTokenizer()
    pages = [
        {"page_number": 1, "text": "CHAPTER I\n" + "alpha beta gamma delta " * 100,
         "ocr_used": False},
        {"page_number": 2, "text": "CHAPTER II\n" + "epsilon zeta eta theta " * 100,
         "ocr_used": True},
    ]
    chunks = structure_aware_chunks(
        pages, target_size=350, max_size=500, min_size=300, tokenizer=tokenizer
    )
    assert chunks
    assert all(1 <= chunk["page_start"] <= chunk["page_end"] <= 2 for chunk in chunks)
    assert all(chunk["token_count"] <= 500 for chunk in chunks)


def test_repeated_header_removed_but_repeated_body_text_preserved():
    pages = [
        {"text": "REGULATOR HEADER\nIntro line\nSecond line\nCommon body wording\nMiddle line\nMore text\nFooter"},
        {"text": "REGULATOR HEADER\nIntro line\nSecond line\nCommon body wording\nMiddle line\nMore text\nFooter"},
        {"text": "REGULATOR HEADER\nIntro line\nSecond line\nCommon body wording\nMiddle line\nMore text\nFooter"},
    ]
    repeated = find_repeated_lines(pages)
    cleaned = clean_page_text(pages[0]["text"], repeated)
    assert "REGULATOR HEADER" not in cleaned
    assert "Common body wording" in cleaned


def test_image_dominant_page_with_weak_text_is_flagged_for_ocr():
    pages = [
        {"page_number": 1, "word_count": 180, "image_coverage": 0.82},
        {"page_number": 2, "word_count": 800, "image_coverage": 0.02},
    ]
    assert detect_scanned_pages(pages, image_text_word_limit=400) == [1]


def test_ocr_disabled_does_not_call_tesseract(monkeypatch, tmp_path):
    import src.ocr as ocr_module

    def fail_if_called(*args, **kwargs):
        raise AssertionError("OCR must not run when disabled")

    monkeypatch.setattr(ocr_module, "ocr_page", fail_if_called)
    pages = [{"page_number": 1, "text": "", "word_count": 0, "has_text": False}]
    result = apply_ocr_to_pages(tmp_path / "unused.pdf", pages, enabled=False)
    assert result[0]["ocr_used"] is False


class FakeTable:
    # Match PyMuPDF's observed column-major cell ordering.
    cells = [
        (0, 0, 50, 20), (0, 20, 50, 40),
        (50, 0, 100, 20), (50, 20, 100, 40),
    ]

    def extract(self):
        # Simulate the known PyMuPDF reconstruction defect.
        return [["Risk", "Multiplier"], ["Medium risk", "15 ."]]


class FakeTableFinder:
    tables = [FakeTable()]


class FakeTablePage:
    def find_tables(self):
        return FakeTableFinder()

    def get_text(self, mode):
        assert mode == "words"
        return [
            (2, 2, 25, 12, "Risk", 0, 0, 0),
            (52, 2, 90, 12, "Multiplier", 0, 0, 1),
            (2, 22, 40, 32, "Medium", 1, 0, 0),
            (41, 22, 49, 32, "risk", 1, 0, 1),
            (52, 22, 65, 32, "1.5", 1, 0, 2),
        ]


def test_table_cells_prefer_native_words_to_corrupted_reconstruction():
    from src.parser import _extract_tables

    tables = _extract_tables(FakeTablePage())

    assert len(tables) == 1
    assert "| Medium risk | 1.5 |" in tables[0]
    assert "15 ." not in tables[0]


def test_table_detection_errors_are_not_silently_ignored():
    import pytest
    from src.parser import _extract_tables

    class BrokenTablePage:
        def find_tables(self):
            raise RuntimeError("table detection failed")

    with pytest.raises(RuntimeError, match="table detection failed"):
        _extract_tables(BrokenTablePage())


def test_long_tables_repeat_headers_and_keep_rows_within_budget():
    from src.chunker import structure_aware_chunks

    pages = [{
        "page_number": 7,
        "ocr_used": True,
        "text": (
            "APPENDIX A\n"
            "[TABLE 1]\n"
            "| Category | Threshold |\n"
            "| --- | --- |\n"
            + "".join(f"| Category {i} | Value {i} |\n" for i in range(1, 13))
        ),
    }]
    chunks = structure_aware_chunks(
        pages, target_size=10, max_size=15, min_size=4
    )

    assert len(chunks) > 1
    table_chunks = [chunk for chunk in chunks if "[TABLE 1]" in chunk["text"]]
    assert len(table_chunks) > 1
    assert any(chunk["text"] == "APPENDIX A" for chunk in chunks)

    for chunk in table_chunks:
        assert chunk["token_count"] <= 15
        assert "| Category | Threshold |" in chunk["text"]
        assert "| --- | --- |" in chunk["text"]
        assert chunk["page_start"] == chunk["page_end"] == 7
        assert chunk["ocr_used"] is True

    body_rows = [
        line for chunk in table_chunks for line in chunk["text"].splitlines()
        if line.startswith("| Category ") and not line.startswith("| Category |")
    ]
    assert len(body_rows) == 12
    assert len(set(body_rows)) == 12


def test_table_row_that_exceeds_budget_is_split_with_context():
    from src.chunker import structure_aware_chunks

    pages = [{
        "page_number": 3,
        "text": (
            "[TABLE 2]\n"
            "| Field | Description |\n"
            "| --- | --- |\n"
            "| Long field | " + "detail " * 30 + "|\n"
        ),
    }]
    chunks = structure_aware_chunks(
        pages, target_size=10, max_size=15, min_size=5
    )

    assert len(chunks) > 1
    assert all(chunk["token_count"] <= 15 for chunk in chunks)
    assert all("[TABLE 2]" in chunk["text"] for chunk in chunks)
    assert all("| Field | Description |" in chunk["text"] for chunk in chunks)


def test_wide_table_header_does_not_fail_when_separator_exceeds_budget():
    from src.chunker import structure_aware_chunks

    header = "| " + " ".join(f"Column{i}" for i in range(1, 11)) + " |"
    separator = "| " + " | ".join(["---"] * 10) + " |"
    pages = [{
        "page_number": 74,
        "text": (
            "[TABLE 1]\n"
            + header + "\n"
            + separator + "\n"
            + "| row | value |\n"
        ),
    }]

    chunks = structure_aware_chunks(
        pages, target_size=20, max_size=20, min_size=5
    )

    assert chunks
    assert all(chunk["token_count"] <= 20 for chunk in chunks)
    assert all(header in chunk["text"] for chunk in chunks)
    assert any("| row | value |" in chunk["text"] for chunk in chunks)
    assert all(separator not in chunk["text"] for chunk in chunks)


def test_table_data_row_is_not_mistaken_for_markdown_separator():
    from src.chunker import structure_aware_chunks

    header = "| Description | Details |"
    data_row = "| 23 | Holding and subsidiary companies |"
    pages = [{
        "page_number": 189,
        "text": "[TABLE 1]\n" + header + "\n" + data_row + "\n",
    }]

    chunks = structure_aware_chunks(
        pages, target_size=50, max_size=100, min_size=5
    )

    assert len(chunks) == 1
    assert header in chunks[0]["text"]
    assert data_row in chunks[0]["text"]


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(char) for char in text]

    def decode(self, token_ids, skip_special_tokens=True):
        return "".join(chr(token_id) for token_id in token_ids)


def test_oversized_first_table_row_is_preserved_in_bounded_continuations():
    tokenizer = CharacterTokenizer()
    first_row = "|" + ("long-cell-content-" * 8) + "|"
    body_row = "| 1 | Example value |"
    pages = [{
        "page_number": 95,
        "ocr_used": False,
        "text": (
            "[TABLE 1]\n"
            + first_row + "\n"
            + "| --- | --- |\n"
            + body_row + "\n"
        ),
    }]

    chunks = structure_aware_chunks(
        pages, target_size=12, max_size=120, min_size=5, tokenizer=tokenizer
    )
    continuation_prefix = "[TABLE 1]\n[FIRST ROW CONTINUATION]\n"
    continuations = [
        chunk for chunk in chunks
        if chunk["text"].startswith(continuation_prefix)
    ]
    body_prefix = (
        "[TABLE 1]\n"
        "[FIRST ROW EXCEEDS CHUNK LIMIT; SEE FIRST ROW CONTINUATION]\n"
    )
    body_chunks = [
        chunk for chunk in chunks if chunk["text"].startswith(body_prefix)
    ]

    assert len(continuations) > 1
    assert "".join(
        chunk["text"][len(continuation_prefix):] for chunk in continuations
    ) == first_row
    assert "".join(
        chunk["text"][len(body_prefix):] for chunk in body_chunks
    ) == body_row
    assert all(chunk["token_count"] <= 120 for chunk in chunks)
    assert all(chunk["page_start"] == chunk["page_end"] == 95 for chunk in chunks)


def test_oversized_table_body_row_is_split_without_losing_characters():
    tokenizer = CharacterTokenizer()
    long_row = "|" + ("body-value-" * 12) + "|"
    prefix = "[TABLE 2]\n| Field | Description |\n| --- | --- |\n"
    pages = [{
        "page_number": 12,
        "text": (
            "[TABLE 2]\n"
            "| Field | Description |\n"
            "| --- | --- |\n"
            + long_row + "\n"
        ),
    }]

    chunks = structure_aware_chunks(
        pages, target_size=10, max_size=100, min_size=5, tokenizer=tokenizer
    )
    row_chunks = [
        chunk for chunk in chunks if chunk["text"].startswith(prefix)
    ]

    assert len(row_chunks) > 1
    assert "".join(
        chunk["text"][len(prefix):] for chunk in row_chunks
    ) == long_row
    assert all(chunk["token_count"] <= 100 for chunk in chunks)
