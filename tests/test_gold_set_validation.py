import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "eval" / "validate_gold_set.py"
FIELDS = [
    "id",
    "question",
    "expected_doc_id",
    "expected_page_start",
    "expected_page_end",
    "is_table_question",
    "is_paraphrased",
]


def write_inputs(tmp_path, *, overflow=False, wrong_table_count=False):
    questions_path = tmp_path / "questions.csv"
    manifest_path = tmp_path / "manifest.csv"

    with questions_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for index in range(1, 26):
            writer.writerow({
                "id": f"q{index:02d}",
                "question": f"Question {index}?",
                "expected_doc_id": "doc_a",
                "expected_page_start": 1,
                "expected_page_end": 11 if overflow and index == 1 else 10,
                "is_table_question": (
                    "true" if index <= (4 if wrong_table_count else 5) else "false"
                ),
                "is_paraphrased": "true" if 6 <= index <= 10 else "false",
            })

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["doc_id", "page_count"])
        writer.writeheader()
        writer.writerow({"doc_id": "doc_a", "page_count": 10})

    return questions_path, manifest_path


def run_validator(questions_path, manifest_path):
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--questions",
            str(questions_path),
            "--manifest",
            str(manifest_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_gold_set_validator_accepts_valid_25_question_set(tmp_path):
    questions, manifest = write_inputs(tmp_path)
    result = run_validator(questions, manifest)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Gold-set validation PASSED." in result.stdout


def test_gold_set_validator_rejects_page_range_beyond_manifest(tmp_path):
    questions, manifest = write_inputs(tmp_path, overflow=True)
    result = run_validator(questions, manifest)

    assert result.returncode == 1
    assert "beyond doc_a's manifest page_count (10)" in result.stdout


def test_gold_set_validator_rejects_wrong_table_question_count(tmp_path):
    questions, manifest = write_inputs(tmp_path, wrong_table_count=True)
    result = run_validator(questions, manifest)

    assert result.returncode == 1
    assert "Expected 5 table questions; found 4." in result.stdout
