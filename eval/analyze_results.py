"""Create per-question and strategy-disagreement summaries from Phase 3 logs."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def first_hit(group: pd.DataFrame) -> int | None:
    hits = group.loc[group["is_correct"].astype(str).str.lower().eq("true"), "rank"]
    return int(hits.min()) if not hits.empty else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default="eval/retrieval_log_phase3.csv")
    parser.add_argument("--questions", default="eval/questions.csv")
    parser.add_argument("--output-dir", default="eval")
    args = parser.parse_args()

    log = pd.read_csv(args.log)
    questions = pd.read_csv(args.questions)
    required = {"question_id", "strategy", "rank", "is_correct", "doc_id", "title",
                "page_start", "page_end", "query_latency_ms"}
    missing = required - set(log.columns)
    if missing:
        raise ValueError(f"Retrieval log missing columns: {sorted(missing)}")
    if set(log["strategy"].unique()) != {"fixed", "structure"}:
        raise ValueError("Expected exactly fixed and structure strategies.")
    if len(questions) != 25 or questions["id"].astype(str).duplicated().any():
        raise ValueError("Expected 25 questions with unique IDs.")
    expected_ids = set(questions["id"].astype(str))
    if set(log["question_id"].astype(str)) != expected_ids:
        raise ValueError("Retrieval log question IDs do not match questions.csv.")

    rows = []
    for question in questions.to_dict("records"):
        qid = str(question["id"])
        result = {"question_id": qid, "question": question["question"],
                  "expected_doc_id": question["expected_doc_id"],
                  "expected_page_start": question["expected_page_start"],
                  "expected_page_end": question["expected_page_end"],
                  "is_table_question": question["is_table_question"],
                  "is_paraphrased": question["is_paraphrased"]}
        for strategy in ("fixed", "structure"):
            group = log[(log["question_id"].astype(str) == qid) &
                        (log["strategy"] == strategy)].copy()
            if group.empty or group["rank"].nunique() != len(group):
                raise ValueError(f"Incomplete or duplicate ranks for {qid}/{strategy}.")
            rank = first_hit(group)
            top = group.sort_values("rank").iloc[0]
            result[f"{strategy}_first_hit_rank"] = rank
            result[f"{strategy}_hit_at_3"] = rank is not None and rank <= 3
            result[f"{strategy}_hit_at_5"] = rank is not None and rank <= 5
            result[f"{strategy}_hit_at_10"] = rank is not None and rank <= 10
            result[f"{strategy}_top1_doc_id"] = top["doc_id"]
            result[f"{strategy}_top1_title"] = top["title"]
            result[f"{strategy}_top1_pages"] = f'{top["page_start"]}-{top["page_end"]}'
            result[f"{strategy}_query_latency_ms"] = float(top["query_latency_ms"])
        a, b = result["fixed_first_hit_rank"], result["structure_first_hit_rank"]
        result["first_hit_rank_gap"] = (
            None if a is None and b is None else
            (11 if a is None else a) - (11 if b is None else b)
        )
        result["strategies_disagree"] = (
            result["fixed_hit_at_10"] != result["structure_hit_at_10"] or
            result["fixed_top1_doc_id"] != result["structure_top1_doc_id"]
        )
        rows.append(result)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    per_question = pd.DataFrame(rows)
    per_question.to_csv(output / "per_question_phase3.csv", index=False)

    disagreements = per_question[per_question["strategies_disagree"]].copy()
    disagreements["absolute_rank_gap"] = disagreements["first_hit_rank_gap"].abs()
    disagreements.sort_values(
        ["absolute_rank_gap", "question_id"],
        ascending=[False, True],
        na_position="last",
    ).drop(columns=["absolute_rank_gap"]).to_csv(
        output / "disagreements_phase3.csv", index=False
    )

    print(f"Per-question summary: {output / 'per_question_phase3.csv'}")
    print(f"Disagreements: {output / 'disagreements_phase3.csv'} ({len(disagreements)} questions)")
    print("Review the disagreement file and select three examples for the report; do not infer causality from rank gaps alone.")


if __name__ == "__main__":
    main()
