import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from answer_validation import (  # noqa: E402
    build_answer_key, build_review_template, parse_required_facts, score_reviews, validate_inputs,
)


def answer(qid="q1"):
    return {
        "question_id": qid, "reference_answer": "The deadline is 10 days.",
        "required_facts": "F1::Upload within 10 days;F2::After account-based relationship starts",
        "answerability": "answerable", "annotation_status": "verified",
    }


def review(qid="q1", strategy="fixed", rank="1", fact_ids="F1;F2"):
    return {
        "question_id": qid, "strategy": strategy, "rank": rank, "chunk_id": "c1",
        "doc_id": "doc", "page_start": "1", "page_end": "1",
        "evidence_class": "complete", "supported_fact_ids": fact_ids,
        "citation_status": "accurate", "source_verified": "yes", "review_notes": "",
    }


def test_parse_required_facts_rejects_duplicate_and_malformed():
    assert list(parse_required_facts("F1::One;F2::Two")) == ["F1", "F2"]
    with pytest.raises(ValueError):
        parse_required_facts("F1::One;F1::Duplicate")
    with pytest.raises(ValueError):
        parse_required_facts("fact without id")


def test_complete_and_partial_support_scoring():
    key = [answer()]
    rows = [review(fact_ids="F1"), review(strategy="structure", fact_ids="F1;F2")]
    scores = score_reviews(key, rows)
    fixed = next(x for x in scores if x["strategy"] == "fixed")
    structure = next(x for x in scores if x["strategy"] == "structure")
    assert fixed["outcome"] == "partial_support" and fixed["fact_coverage"] == 0.5
    assert structure["outcome"] == "complete_support" and structure["citation_accuracy"] == 1.0


def test_unknown_fact_ids_and_unverified_annotation_fail():
    with pytest.raises(ValueError, match="unknown supported fact"):
        score_reviews([answer()], [review(fact_ids="F9")])
    bad = answer()
    bad["annotation_status"] = "pending"
    assert any("must be verified" in e for e in validate_inputs([bad], [review()]))


def test_insufficient_source_requires_explicit_abstention_evidence():
    key = answer()
    key.update(reference_answer="", required_facts="", answerability="insufficient_source")
    row = review(fact_ids="")
    row["evidence_class"] = "insufficient"
    scores = score_reviews([key], [row])
    assert all(x["outcome"] == "abstention_supported" for x in scores)


def test_build_templates(tmp_path):
    gold = tmp_path / "gold.csv"
    gold.write_text(
        "id,question,expected_doc_id,expected_page_start,expected_page_end,gold_passages,label_status,include_in_headline\n"
        "q1,Question?,d,1,1,d:1-1,verified,true\n"
        "q2,Invalid?,d,1,1,d:1-1,invalid,false\n",
        encoding="utf-8",
    )
    answer_path = tmp_path / "answer.csv"
    assert build_answer_key(gold, answer_path) == 1
    assert "pending" in answer_path.read_text()
    log = tmp_path / "log.csv"
    log.write_text(
        "question_id,strategy,rank,chunk_id,doc_id,page_start,page_end\n"
        "q1,fixed,1,c1,d,1,1\nq1,fixed,2,c2,d,2,2\n",
        encoding="utf-8",
    )
    review_path = tmp_path / "review.csv"
    assert build_review_template(log, review_path, top_k=1) == 1
