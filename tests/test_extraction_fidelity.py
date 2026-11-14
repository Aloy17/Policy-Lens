from eval.extraction_fidelity import CASES, inspect_case, run


def test_fidelity_cases_cover_tables_and_scanned_ocr_references():
    kinds = {case["kind"] for case in CASES}
    assert {"table", "wide_table", "ocr_reference"}.issubset(kinds)
    assert len(CASES) == 7


def test_inspect_case_reports_missing_pdf_without_crashing(tmp_path):
    result = inspect_case(tmp_path, CASES[0])
    assert result["status"] == "missing_pdf"
    assert result["case_id"] == "S03_depository_risk_table"


def test_run_reports_unavailable_cases_explicitly(tmp_path):
    report = run(tmp_path)
    assert report["summary"] == {
        "cases": 7,
        "passed": 0,
        "failed": 0,
        "unavailable": 7,
    }
    assert len(report["manual_review_required"]) >= 3


def test_ocr_score_rejects_empty_reference():
    import pytest
    from eval.ocr_accuracy import score

    with pytest.raises(ValueError, match="at least one word"):
        score("", "some OCR output")


def test_inspect_case_checks_required_and_forbidden_text(monkeypatch, tmp_path):
    import eval.extraction_fidelity as fidelity

    case = {
        "case_id": "fixture_table",
        "doc_id": "fixture",
        "page": 1,
        "kind": "table",
        "required": ["Medium risk", "1.5"],
        "forbidden": ["15 ."],
        "description": "fixture",
    }
    (tmp_path / "fixture.pdf").touch()
    monkeypatch.setattr(
        fidelity,
        "parse_pdf",
        lambda _path: [{
            "page_number": 1,
            "text": "Medium risk 1.5",
            "table_count": 1,
            "word_count": 3,
            "image_coverage": 0.0,
        }],
    )

    result = fidelity.inspect_case(tmp_path, case)

    assert result["status"] == "pass"
    assert result["missing_required"] == []
    assert result["forbidden_found"] == []


def test_ocr_reference_case_uses_ocr_fallback(monkeypatch, tmp_path):
    import eval.extraction_fidelity as fidelity

    case = {
        "case_id": "fixture_ocr",
        "doc_id": "fixture",
        "page": 2,
        "kind": "ocr_reference",
        "required": ["recognized legal text"],
        "forbidden": [],
        "description": "fixture OCR",
    }
    (tmp_path / "fixture.pdf").touch()
    page = {
        "page_number": 2,
        "text": "weak embedded layer",
        "word_count": 3,
        "image_coverage": 0.9,
        "table_count": 0,
    }
    monkeypatch.setattr(fidelity, "parse_pdf", lambda _path: [page])

    def fake_ocr(_path, pages, enabled=True):
        assert pages == [page]
        assert enabled is True
        return [{**page, "text": "recognized legal text", "ocr_used": True}]

    monkeypatch.setattr(fidelity, "apply_ocr_to_pages", fake_ocr)

    result = fidelity.inspect_case(tmp_path, case)

    assert result["status"] == "pass"
    assert result["ocr_used"] is True
    assert result["ocr_candidate"] is True
