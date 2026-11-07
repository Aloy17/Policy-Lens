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
        {"text": "REGULATOR HEADER\nCommon body wording\nPage one"},
        {"text": "REGULATOR HEADER\nCommon body wording\nPage two"},
        {"text": "REGULATOR HEADER\nCommon body wording\nPage three"},
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
