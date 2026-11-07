from src.chunker import fixed_size_chunks, structure_aware_chunks
from src.metadata import calculate_file_hash
from eval.evaluate import page_range_matches


def test_fixed_chunks_have_expected_size():
    pages = [
        {
            "page_number": 1,
            "text": "word " * 1200,
            "ocr_used": False,
        }
    ]

    chunks = fixed_size_chunks(pages, chunk_size=500, overlap=50)

    assert len(chunks) > 1
    assert all(len(chunk["text"].split()) <= 500 for chunk in chunks)


def test_structure_chunks_return_chunks():
    pages = [
        {
            "page_number": 1,
            "text": (
                "CHAPTER I\n"
                + ("This is regulatory content. " * 120)
            ),
            "ocr_used": False,
        },
        {
            "page_number": 2,
            "text": (
                "CHAPTER II\n"
                + ("More regulatory content. " * 120)
            ),
            "ocr_used": False,
        },
    ]

    chunks = structure_aware_chunks(
        pages,
        target_size=100,
        max_size=150,
        min_size=50,
    )

    assert len(chunks) > 0
    assert all(chunk["text"].strip() for chunk in chunks)


def test_source_hash_is_stable(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"PolicyLens test content")

    first = calculate_file_hash(pdf)
    second = calculate_file_hash(pdf)

    assert first == second
    assert len(first) == 64


def test_page_range_matches():
    metadata = {
        "page_start": 22,
        "page_end": 24,
    }

    assert page_range_matches(metadata, 22, 24)
    assert page_range_matches(metadata, 23, 25)
    assert not page_range_matches(metadata, 30, 35)


def test_source_hash_changes_when_file_changes(tmp_path):
    pdf = tmp_path / "test.pdf"

    pdf.write_bytes(b"original content")
    first = calculate_file_hash(pdf)

    pdf.write_bytes(b"changed content")
    second = calculate_file_hash(pdf)

    assert first != second
