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
