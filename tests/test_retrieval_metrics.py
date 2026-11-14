import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))

from retrieval_metrics import (  # noqa: E402
    MalformedMetadataError, Passage, aggregate, is_relevant, matches_passage, parse_passages, score_question,
)
import run_retrieval_benchmark as bench  # noqa: E402
import validate_gold_v2 as v2  # noqa: E402


def meta(doc, start, end=None):
    return {"doc_id": doc, "page_start": start, "page_end": end if end is not None else start}


GOLD = [Passage("doc_a", 10, 11)]


# ---- relevance by document ID and inclusive page range -------------------

@pytest.mark.parametrize("doc,start,end,expected", [
    ("doc_a", 10, 10, True),    # touches first gold page
    ("doc_a", 11, 11, True),    # touches last gold page (inclusive)
    ("doc_a", 9, 10, True),     # overlaps from below
    ("doc_a", 11, 12, True),    # overlaps from above
    ("doc_a", 8, 20, True),     # chunk spans the gold range
    ("doc_a", 9, 9, False),     # adjacent below
    ("doc_a", 12, 12, False),   # adjacent above
    ("doc_b", 10, 11, False),   # right pages, wrong document
])
def test_relevance_uses_doc_id_and_inclusive_overlap(doc, start, end, expected):
    assert matches_passage(meta(doc, start, end), GOLD[0]) is expected


def test_string_page_numbers_are_accepted():
    assert matches_passage({"doc_id": "doc_a", "page_start": "10", "page_end": "10"}, GOLD[0])


# ---- metrics --------------------------------------------------------------

def test_metrics_known_values():
    results = [meta("doc_x", 1), meta("doc_a", 10), meta("doc_x", 2), meta("doc_a", 11), meta("doc_x", 3)]
    s = score_question(results, GOLD, ks=(3, 5, 10))
    assert s["first_relevant_rank"] == 2 and s["rr"] == 0.5
    assert s["hit@3"] == 1.0 and s["hit@5"] == 1.0
    assert s["precision@3"] == pytest.approx(1 / 3)
    assert s["precision@5"] == pytest.approx(2 / 5)
    assert s["precision@10"] == pytest.approx(2 / 10)  # denominator is k, not results returned


def test_hit_and_recall_miss_outside_k():
    results = [meta("doc_x", i) for i in range(1, 6)] + [meta("doc_a", 10)]
    s = score_question(results, GOLD, ks=(3, 5, 10))
    assert (s["hit@3"], s["hit@5"], s["hit@10"]) == (0.0, 0.0, 1.0)
    assert (s["recall@3"], s["recall@5"], s["recall@10"]) == (0.0, 0.0, 1.0)
    assert s["rr"] == pytest.approx(1 / 6)


def test_no_relevant_results_gives_zero_everywhere():
    s = score_question([meta("doc_x", 1)] * 10, GOLD)
    assert s["rr"] == 0.0 and s["first_relevant_rank"] is None
    assert all(s[f"{m}@{k}"] == 0.0 for m in ("hit", "recall", "precision") for k in (3, 5, 10))


def test_empty_retrieval_results():
    s = score_question([], GOLD)
    assert s["rr"] == 0.0 and s["retrieved"] == 0
    assert all(s[f"{m}@{k}"] == 0.0 for m in ("hit", "recall", "precision") for k in (3, 5, 10))
    agg = aggregate([s])
    assert agg["empty_result_questions"] == 1 and agg["mrr"] == 0.0


def test_aggregate_rejects_empty_set():
    with pytest.raises(ValueError):
        aggregate([])


def test_aggregate_means():
    a = score_question([meta("doc_a", 10)], GOLD)                        # rr 1
    b = score_question([meta("doc_x", 1), meta("doc_a", 10)], GOLD)      # rr .5
    agg = aggregate([a, b])
    assert agg["mrr"] == pytest.approx(0.75)
    assert agg["hit@3"] == 1.0
    assert agg["precision@3"] == pytest.approx((1 / 3 + 1 / 3) / 2)


# ---- multiple relevant passages ------------------------------------------

MULTI = [Passage("doc_a", 94, 94), Passage("doc_a", 95, 95), Passage("doc_a", 32, 32)]


def test_multi_passage_recall_needs_every_passage_but_hit_needs_one():
    results = [meta("doc_a", 95), meta("doc_x", 1), meta("doc_a", 94), meta("doc_x", 2), meta("doc_a", 32)]
    s = score_question(results, MULTI, ks=(1, 3, 5))
    assert s["hit@1"] == 1.0
    assert s["recall@1"] == pytest.approx(1 / 3)
    assert s["recall@3"] == pytest.approx(2 / 3)
    assert s["recall@5"] == 1.0
    assert s["precision@5"] == pytest.approx(3 / 5)


def test_one_chunk_spanning_two_passages_covers_both():
    s = score_question([meta("doc_a", 94, 95)], MULTI[:2], ks=(3,))
    assert s["recall@3"] == 1.0 and s["precision@3"] == pytest.approx(1 / 3)


def test_duplicate_hits_on_one_passage_do_not_inflate_recall():
    s = score_question([meta("doc_a", 94), meta("doc_a", 94), meta("doc_a", 94)], MULTI, ks=(3,))
    assert s["recall@3"] == pytest.approx(1 / 3)
    assert s["precision@3"] == 1.0


# ---- malformed metadata ---------------------------------------------------

BAD = [
    None, {}, {"doc_id": "doc_a"}, {"page_start": 10, "page_end": 10},
    {"doc_id": "doc_a", "page_start": "x", "page_end": 10},
    {"doc_id": "doc_a", "page_start": 12, "page_end": 10},
    {"doc_id": "doc_a", "page_start": 0, "page_end": 0},
    {"doc_id": "", "page_start": 10, "page_end": 10},
    {"doc_id": "doc_a", "page_start": True, "page_end": True},
]


@pytest.mark.parametrize("bad", BAD)
def test_malformed_metadata_is_never_relevant(bad):
    assert not is_relevant(bad, GOLD)


def test_malformed_metadata_counted_in_lenient_mode_and_raises_in_strict():
    s = score_question(BAD[:3] + [meta("doc_a", 10)], GOLD)
    assert s["malformed_results"] == 3 and s["first_relevant_rank"] == 4
    with pytest.raises(MalformedMetadataError):
        score_question(BAD[:1], GOLD, strict=True)
    with pytest.raises(MalformedMetadataError):
        matches_passage({}, GOLD[0], strict=True)


# ---- input validation -----------------------------------------------------

def test_parse_passages():
    assert parse_passages("d:1-2;d2:5-5") == [Passage("d", 1, 2), Passage("d2", 5, 5)]
    for bad in ("", "d", "d:5", "d:5-3", "d:0-1", ":1-2"):
        with pytest.raises(ValueError):
            parse_passages(bad)


def test_k_and_passage_validation():
    with pytest.raises(ValueError):
        score_question([], [])
    with pytest.raises(ValueError):
        score_question([], GOLD, ks=(0,))


# ---- runner with a fake store --------------------------------------------

class FakeSearcher:
    def __init__(self, metas):
        self.metas = metas

    def count(self):
        return len(self.metas)

    def query(self, embedding, top_k):
        m = self.metas[:top_k]
        return {"ids": [[f"c{i}" for i in range(len(m))]], "documents": [[f"text {i}" for i in range(len(m))]],
                "metadatas": [m], "distances": [[0.1 * (i + 1) for i in range(len(m))]]}


def _questions():
    rows = [{
        "id": "q1", "question": "Q?", "expected_doc_id": "doc_a", "expected_page_start": "10", "expected_page_end": "11",
        "is_table_question": "false", "is_paraphrased": "false", "gold_passages": "doc_a:10-11", "passage_terms": "t",
        "requires_multiple_passages": "false", "categories": "direct", "label_status": "verified",
        "include_in_headline": "true", "source_origin": "t", "validation_notes": "",
    }]
    for r in rows:
        r["_passages"] = parse_passages(r["gold_passages"])
        r["_v1_passage"] = Passage("doc_a", 10, 11)
        r["_categories"] = {"direct"}
    return rows


def test_runner_logs_chunk_ids_scores_and_relevance():
    qs = _questions()
    searchers = {"fixed": FakeSearcher([meta("doc_x", 1)] * 10),
                 "structure": FakeSearcher([meta("doc_a", 10)] + [meta("doc_x", 1)] * 9)}
    log, scores = bench.run_benchmark(qs, {"q1": [0.0]}, searchers, top_k=10)
    assert len(log) == 20
    top = next(r for r in log if r["strategy"] == "structure" and r["rank"] == 1)
    assert top["is_relevant"] and top["chunk_id"] == "c0" and top["distance"] == pytest.approx(0.1)
    assert top["similarity"] == pytest.approx(0.9)
    assert scores["fixed"]["q1"]["rr"] == 0.0 and scores["structure"]["q1"]["rr"] == 1.0
    rows = bench.per_question_table(qs, scores)
    assert rows[0]["outcome_top10"] == "only_structure"


def test_runner_handles_empty_results_and_rejects_small_top_k():
    qs = _questions()
    log, scores = bench.run_benchmark(qs, {"q1": [0.0]}, {"fixed": FakeSearcher([]), "structure": FakeSearcher([])}, 10)
    assert log == [] and scores["fixed"]["q1"]["rr"] == 0.0
    with pytest.raises(ValueError):
        bench.run_benchmark(qs, {"q1": [0.0]}, {"fixed": FakeSearcher([])}, top_k=5)


def test_runner_flags_malformed_metadata_in_log():
    qs = _questions()
    log, _ = bench.run_benchmark(qs, {"q1": [0.0]}, {"fixed": FakeSearcher([{}, meta("doc_a", 10)])}, 10)
    assert "malformed_metadata" in log[0]["notes"] and log[1]["notes"] == ""


# ---- v2 gold-set validation ----------------------------------------------

MANIFEST = {"doc_a": 100, "doc_b": 5}


def gold_row(**over):
    row = {
        "id": "q1", "question": "What?", "expected_doc_id": "doc_a", "expected_page_start": "1", "expected_page_end": "1",
        "is_table_question": "false", "is_paraphrased": "false", "gold_passages": "doc_a:1-1", "passage_terms": "x",
        "requires_multiple_passages": "false", "categories": "direct", "label_status": "verified",
        "include_in_headline": "true", "source_origin": "t", "validation_notes": "",
    }
    row.update(over)
    return row


def test_v2_valid_row_passes():
    assert v2.validate_structure([gold_row()], MANIFEST) == []


@pytest.mark.parametrize("over,fragment", [
    ({"gold_passages": "doc_a:1-101", "passage_terms": "x"}, "exceeds"),
    ({"gold_passages": "doc_z:1-1"}, "absent from manifest"),
    ({"gold_passages": "doc_a:5-3"}, "Malformed passage spec"),
    ({"label_status": "maybe"}, "label_status"),
    ({"categories": "direct|bogus"}, "unknown"),
    ({"gold_passages": "doc_a:1-1;doc_a:2-2", "passage_terms": "x;y"}, "requires_multiple_passages"),
    ({"passage_terms": "x;y"}, "one ';'"),
    ({"is_table_question": "true"}, "is_table_question"),
    ({"label_status": "invalid"}, "invalid questions"),
    ({"question": " "}, "empty question"),
])
def test_v2_structural_errors_detected(over, fragment):
    errors = v2.validate_structure([gold_row(**over)], MANIFEST)
    assert any(fragment in e for e in errors), errors


def test_v2_duplicate_ids_and_questions_detected():
    errors = v2.validate_structure([gold_row(), gold_row()], MANIFEST)
    assert any("duplicate id" in e for e in errors) and any("duplicate question" in e for e in errors)


def test_v2_evidence_check_flags_wrong_page(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "doc_a.pdf"
    document = pymupdf.open()
    for text in ("alpha page", "the needle is here", "gamma page"):
        document.new_page().insert_text((72, 72), text)
    document.save(str(pdf))
    document.close()
    good = gold_row(gold_passages="doc_a:2-2", passage_terms="needle is here")
    bad = gold_row(id="q2", question="Other?", gold_passages="doc_a:3-3", passage_terms="needle is here")
    errors, details = v2.validate_evidence([good, bad], tmp_path, ocr=False)
    assert len(errors) == 1 and "q2" in errors[0]
    assert [d["result"] for d in details] == ["PASS", "FAIL"]


def test_committed_v2_dataset_is_structurally_valid():
    path = ROOT / "eval" / "benchmark_2026-11-14" / "gold_questions_v2.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == v2.REQUIRED_COLUMNS
        rows = list(reader)
    manifest = v2.load_manifest(ROOT / "data" / "manifest.csv")
    assert v2.validate_structure(rows, manifest) == []
    ids = [r["id"] for r in rows]
    assert ids[:25] == [f"q{i:02d}" for i in range(1, 26)]  # original IDs preserved
    original = {r["id"]: r for r in csv.DictReader((ROOT / "eval" / "questions.csv").open(encoding="utf-8"))}
    for qid, orig in original.items():
        row = next(r for r in rows if r["id"] == qid)
        assert row["question"] == orig["question"]
        assert (row["expected_page_start"], row["expected_page_end"]) == (orig["expected_page_start"], orig["expected_page_end"])



def test_runner_rejects_mismatched_chroma_result_arrays():
    class BrokenSearcher(FakeSearcher):
        def query(self, embedding, top_k):
            return {
                "ids": [["c1", "c2"]],
                "documents": [["one"]],
                "metadatas": [[meta("doc_a", 10)]],
                "distances": [[0.1]],
            }

    with pytest.raises(ValueError, match="inconsistent Chroma result lengths"):
        bench.run_benchmark(
            _questions(), {"q1": [0.0]},
            {"fixed": BrokenSearcher([]), "structure": FakeSearcher([])}, 10
        )


def test_evidence_term_proxy_requires_all_terms_in_same_chunk():
    passage = Passage("doc_a", 10, 11)
    metadata = meta("doc_a", 10, 11)
    assert bench.evidence_passages_for_result(
        "The customer identification records are confidential.", metadata,
        [passage], ["customer identification|records are confidential"]
    ) == {0}
    assert not bench.evidence_passages_for_result(
        "The customer identification process is described. Confidential records are retained.",
        metadata, [passage], ["customer identification|records are confidential"]
    )


def test_evidence_term_proxy_does_not_overcredit_second_passage():
    passages = [Passage("doc_a", 10, 10), Passage("doc_a", 11, 11)]
    scores = bench.score_evidence_term_proxy(
        ["The header is Category III only.", "No matching evidence here."],
        [meta("doc_a", 10, 11), meta("doc_x", 1)],
        passages, ["Category III|header", "mandatory|proof of identity"], ks=(1, 2)
    )
    assert scores["recall@1"] == pytest.approx(0.5)
    assert scores["recall@2"] == pytest.approx(0.5)


def test_pdf_evidence_skips_are_reported_and_fail_by_default(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf = pdf_dir / "doc_a.pdf"
    pymupdf = pytest.importorskip("pymupdf")
    document = pymupdf.open()
    document.new_page()
    document.save(str(pdf))
    document.close()

    row = gold_row()
    row["passage_terms"] = "not present"
    errors, details = v2.validate_evidence([row], pdf_dir, ocr=False)
    assert errors == []
    assert details[0]["result"] == "SKIPPED"
