"""Validate the structure and required category counts of the Phase 3 gold set."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

REQUIRED_COLUMNS = {
    "id",
    "question",
    "expected_doc_id",
    "expected_page_start",
    "expected_page_end",
    "is_table_question",
    "is_paraphrased",
}
EXPECTED_IDS = [f"q{i:02d}" for i in range(1, 26)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default="eval/questions.csv")
    args = parser.parse_args()

    path = Path(args.questions)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or set(reader.fieldnames) != REQUIRED_COLUMNS:
            raise SystemExit(
                f"Invalid columns. Expected exactly: {', '.join(sorted(REQUIRED_COLUMNS))}"
            )
        rows = list(reader)

    errors: list[str] = []
    ids = [row["id"] for row in rows]
    if ids != EXPECTED_IDS:
        errors.append("IDs must appear exactly once and in order from q01 through q25.")

    for row in rows:
        if not row["question"].strip():
            errors.append(f"{row['id']}: question is empty.")
        if not row["expected_doc_id"].strip():
            errors.append(f"{row['id']}: expected_doc_id is empty.")
        try:
            start = int(row["expected_page_start"])
            end = int(row["expected_page_end"])
            if start < 1 or end < start:
                raise ValueError
        except ValueError:
            errors.append(f"{row['id']}: invalid inclusive PDF page range.")

        for field in ("is_table_question", "is_paraphrased"):
            if row[field].lower() not in {"true", "false"}:
                errors.append(f"{row['id']}: {field} must be true or false.")

    table_count = sum(row["is_table_question"].lower() == "true" for row in rows)
    paraphrase_count = sum(row["is_paraphrased"].lower() == "true" for row in rows)
    if len(rows) != 25:
        errors.append(f"Expected 25 questions; found {len(rows)}.")
    if table_count != 5:
        errors.append(f"Expected 5 table questions; found {table_count}.")
    if paraphrase_count != 5:
        errors.append(f"Expected 5 paraphrased questions; found {paraphrase_count}.")

    if errors:
        print("Gold-set structural validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Gold-set structural validation PASSED.")
    print(f"Questions: {len(rows)}")
    print(f"Table questions: {table_count}")
    print(f"Paraphrased questions: {paraphrase_count}")
    print("IDs: q01–q25, unique and ordered")
    print("Page ranges: positive, inclusive, and well-formed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
