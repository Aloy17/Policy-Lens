"""Human-reviewed, answer-supporting evidence evaluation for PolicyLens.

This module deliberately does not generate legal answers. It validates a
human-authored answer key and scores human assessments of retrieved passages.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ANSWER_KEY_FIELDS = {
    "question_id", "reference_answer", "required_facts", "answerability",
    "annotation_status",
}
REVIEW_FIELDS = {
    "question_id", "strategy", "rank", "chunk_id", "doc_id", "page_start",
    "page_end", "evidence_class", "supported_fact_ids", "citation_status",
    "source_verified", "review_notes",
}
EVIDENCE_CLASSES = {"complete", "partial", "irrelevant", "insufficient"}
CITATION_STATUSES = {"accurate", "inaccurate", "overinclusive", "missing", "not_applicable"}
ANSWERABILITY = {"answerable", "insufficient_source"}
STRATEGIES = {"fixed", "structure"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_answer_key(gold_path: Path, output_path: Path) -> int:
    """Create a deliberately unannotated answer-key template from valid gold rows."""
    gold = _read_csv(gold_path)
    rows = []
    for q in gold:
        if q.get("label_status") == "invalid" or q.get("include_in_headline", "").lower() != "true":
            continue
        rows.append({
            "question_id": q["id"],
            "question": q["question"],
            "reference_answer": "",
            "required_facts": "",
            "gold_passages": q["gold_passages"],
            "answerability": "answerable",
            "annotation_status": "pending",
            "review_notes": "",
        })
    fields = ["question_id", "question", "reference_answer", "required_facts",
              "gold_passages", "answerability", "annotation_status", "review_notes"]
    _write_csv(output_path, rows, fields)
    return len(rows)


def build_review_template(log_path: Path, output_path: Path, top_k: int = 10) -> int:
    """Create one manual review row per retrieved chunk, preserving its citation."""
    if top_k < 1:
        raise ValueError("top_k must be >= 1.")
    source = _read_csv(log_path)
    required = {"question_id", "strategy", "rank", "doc_id", "page_start", "page_end"}
    if source and not required.issubset(source[0]):
        raise ValueError(f"Retrieval log missing columns: {sorted(required - set(source[0]))}")
    rows = []
    for item in source:
        rank = int(item["rank"])
        if rank > top_k:
            continue
        rows.append({
            "question_id": item["question_id"],
            "strategy": item["strategy"],
            "rank": rank,
            "chunk_id": item.get("chunk_id", ""),
            "doc_id": item.get("doc_id", ""),
            "page_start": item.get("page_start", ""),
            "page_end": item.get("page_end", ""),
            "evidence_class": "",
            "supported_fact_ids": "",
            "citation_status": "",
            "source_verified": "",
            "review_notes": "",
        })
    fields = ["question_id", "strategy", "rank", "chunk_id", "doc_id", "page_start",
              "page_end", "evidence_class", "supported_fact_ids", "citation_status",
              "source_verified", "review_notes"]
    _write_csv(output_path, rows, fields)
    return len(rows)


def parse_required_facts(value: str) -> dict[str, str]:
    facts = {}
    for item in filter(None, (part.strip() for part in value.split(";"))):
        if "::" not in item:
            raise ValueError(f"Required fact must use FACT_ID::description: {item}")
        fact_id, description = (part.strip() for part in item.split("::", 1))
        if not fact_id or not description or fact_id in facts:
            raise ValueError(f"Invalid or duplicate required fact: {item}")
        facts[fact_id] = description
    return facts


def validate_inputs(answer_key: list[dict[str, str]], reviews: list[dict[str, str]]) -> list[str]:
    errors = []
    seen = set()
    for row in answer_key:
        qid = row.get("question_id", "").strip()
        if not qid or qid in seen:
            errors.append(f"Answer key: missing or duplicate question_id {qid!r}.")
        seen.add(qid)
        if row.get("annotation_status") != "verified":
            errors.append(f"{qid}: annotation_status must be verified.")
        if row.get("answerability") not in ANSWERABILITY:
            errors.append(f"{qid}: invalid answerability.")
        if row.get("answerability") == "answerable":
            if not row.get("reference_answer", "").strip():
                errors.append(f"{qid}: reference_answer is required.")
            try:
                facts = parse_required_facts(row.get("required_facts", ""))
                if not facts:
                    errors.append(f"{qid}: at least one required fact is required.")
            except ValueError as exc:
                errors.append(f"{qid}: {exc}")
        elif row.get("required_facts", "").strip():
            errors.append(f"{qid}: insufficient_source rows must not define required facts.")

    answer_ids = {r.get("question_id", "") for r in answer_key}
    review_keys = set()
    for row in reviews:
        qid = row.get("question_id", "").strip()
        key = (qid, row.get("strategy", ""), row.get("rank", ""))
        if key in review_keys:
            errors.append(f"{qid}: duplicate review row for {key[1]} rank {key[2]}.")
        review_keys.add(key)
        if qid not in answer_ids:
            errors.append(f"{qid}: review has no matching answer-key row.")
        if row.get("strategy") not in STRATEGIES:
            errors.append(f"{qid}: invalid strategy {row.get('strategy')!r}.")
        try:
            if int(row.get("rank", "")) < 1:
                raise ValueError
        except ValueError:
            errors.append(f"{qid}: rank must be a positive integer.")
        if row.get("evidence_class") not in EVIDENCE_CLASSES:
            errors.append(f"{qid}: evidence_class must be one of {sorted(EVIDENCE_CLASSES)}.")
        if row.get("citation_status") not in CITATION_STATUSES:
            errors.append(f"{qid}: invalid citation_status.")
        if row.get("source_verified", "").lower() not in {"yes", "no"}:
            errors.append(f"{qid}: source_verified must be yes or no.")
        if row.get("citation_status") == "accurate" and row.get("source_verified", "").lower() != "yes":
            errors.append(f"{qid}: an accurate citation must be verified against the source PDF.")
    return errors


def score_reviews(answer_key: list[dict[str, str]], reviews: list[dict[str, str]]) -> list[dict]:
    """Score fact coverage and citation fidelity per question and strategy."""
    errors = validate_inputs(answer_key, reviews)
    if errors:
        raise ValueError("Input validation failed:\n" + "\n".join(errors))
    key_by_id = {r["question_id"]: r for r in answer_key}
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in reviews:
        grouped[(row["question_id"], row["strategy"])].append(row)

    output = []
    for qid, key in key_by_id.items():
        facts = parse_required_facts(key.get("required_facts", ""))
        for strategy in ("fixed", "structure"):
            rows = grouped.get((qid, strategy), [])
            supported = set()
            for row in rows:
                supported.update(filter(None, row.get("supported_fact_ids", "").split(";")))
            unknown = supported - facts.keys()
            if unknown:
                raise ValueError(f"{qid}/{strategy}: unknown supported fact IDs: {sorted(unknown)}")
            covered = len(supported)
            total = len(facts)
            if key["answerability"] == "insufficient_source":
                outcome = "abstention_supported" if any(r["evidence_class"] == "insufficient" for r in rows) else "not_demonstrated"
            elif total and covered == total:
                outcome = "complete_support"
            elif covered:
                outcome = "partial_support"
            else:
                outcome = "no_support"
            citation_rows = [r for r in rows if r["citation_status"] != "not_applicable"]
            citation_denominator = len(citation_rows)
            citation_accurate = sum(r["citation_status"] == "accurate" for r in citation_rows)
            citation_rate = citation_accurate / citation_denominator if citation_denominator else None
            output.append({
                "question_id": qid, "strategy": strategy, "answerability": key["answerability"],
                "outcome": outcome, "required_fact_count": total, "supported_fact_count": covered,
                "fact_coverage": covered / total if total else None,
                "citation_assessments": citation_denominator,
                "accurate_citations": citation_accurate, "citation_accuracy": citation_rate,
                "reviewed_chunks": len(rows),
                "unverified_source_chunks": sum(r["source_verified"] != "yes" for r in rows),
            })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and score human-reviewed PolicyLens answer evidence.")
    sub = parser.add_subparsers(dest="command", required=True)
    build_key = sub.add_parser("build-answer-key")
    build_key.add_argument("--gold", default="eval/benchmark_2026-11-14/gold_questions_v2.csv")
    build_key.add_argument("--output", default="eval/task3/answer_key.csv")
    build_review = sub.add_parser("build-review-template")
    build_review.add_argument("--log", required=True)
    build_review.add_argument("--output", default="eval/task3/evidence_review.csv")
    build_review.add_argument("--top-k", type=int, default=10)
    validate = sub.add_parser("validate")
    validate.add_argument("--answer-key", default="eval/task3/answer_key.csv")
    validate.add_argument("--reviews", default="eval/task3/evidence_review.csv")
    score = sub.add_parser("score")
    score.add_argument("--answer-key", default="eval/task3/answer_key.csv")
    score.add_argument("--reviews", default="eval/task3/evidence_review.csv")
    score.add_argument("--output", default="eval/task3/answer_validation_scores.csv")
    args = parser.parse_args()

    if args.command == "build-answer-key":
        count = build_answer_key(Path(args.gold), Path(args.output))
        print(f"Created {count} pending answer-key rows: {args.output}")
        print("Complete reference answers and atomic required facts before scoring.")
    elif args.command == "build-review-template":
        count = build_review_template(Path(args.log), Path(args.output), args.top_k)
        print(f"Created {count} pending evidence-review rows: {args.output}")
    else:
        answer_key, reviews = _read_csv(Path(args.answer_key)), _read_csv(Path(args.reviews))
        errors = validate_inputs(answer_key, reviews)
        if errors:
            print(json.dumps({"valid": False, "errors": errors}, indent=2))
            raise SystemExit(1)
        if args.command == "validate":
            print(json.dumps({"valid": True, "questions": len(answer_key), "review_rows": len(reviews)}, indent=2))
        else:
            rows = score_reviews(answer_key, reviews)
            fields = list(rows[0]) if rows else []
            _write_csv(Path(args.output), rows, fields)
            print(f"Wrote {len(rows)} question-strategy scores to {args.output}")


if __name__ == "__main__":
    main()
