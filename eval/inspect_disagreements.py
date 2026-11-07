"""Export detailed evidence for selected Phase 3 retrieval disagreements.

Run from the repository root after eval/retrieval_log_phase3.csv exists:
    PYTHONPATH=. python eval/inspect_disagreements.py

The script does not access or modify Chroma. It reads the saved retrieval log
and canonical question set, then exports the top-k passages for the selected
report examples so their relevance can be reviewed directly.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_CASES = ("q04", "q17", "q13")
REQUIRED_LOG_COLUMNS = {
    "question_id", "question", "strategy", "rank", "score", "doc_id",
    "title", "page_start", "page_end", "section_title", "is_correct",
    "preview", "query_latency_ms",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default="eval/retrieval_log_phase3.csv")
    parser.add_argument("--questions", default="eval/questions.csv")
    parser.add_argument("--output", default="eval/selected_disagreement_evidence.csv")
    parser.add_argument(
        "--question-ids", nargs="+", default=list(DEFAULT_CASES),
        help="Question IDs to export (default: q04 q17 q13).",
    )
    parser.add_argument(
        "--top-k", type=int, default=10,
        help="Maximum ranked passages per question and strategy.",
    )
    args = parser.parse_args()

    if args.top_k < 1:
        raise ValueError("--top-k must be positive.")

    log = pd.read_csv(args.log)
    questions = pd.read_csv(args.questions)
    missing = REQUIRED_LOG_COLUMNS - set(log.columns)
    if missing:
        raise ValueError(f"Retrieval log missing columns: {sorted(missing)}")

    question_ids = set(questions["id"].astype(str))
    unknown = set(args.question_ids) - question_ids
    if unknown:
        raise ValueError(f"Unknown question IDs: {sorted(unknown)}")

    records = []
    for question_id in args.question_ids:
        question = questions.loc[
            questions["id"].astype(str) == question_id
        ].iloc[0]
        subset = log[log["question_id"].astype(str) == question_id].copy()

        if set(subset["strategy"].unique()) != {"fixed", "structure"}:
            raise ValueError(
                f"{question_id}: expected both fixed and structure results."
            )

        for strategy in ("fixed", "structure"):
            ranked = subset[subset["strategy"] == strategy].sort_values("rank")
            if ranked.empty:
                raise ValueError(f"{question_id}/{strategy}: no retrieval rows.")

            for _, hit in ranked.head(args.top_k).iterrows():
                records.append({
                    "question_id": question_id,
                    "question": question["question"],
                    "expected_doc_id": question["expected_doc_id"],
                    "expected_page_start": question["expected_page_start"],
                    "expected_page_end": question["expected_page_end"],
                    "strategy": strategy,
                    "rank": int(hit["rank"]),
                    "score": hit["score"],
                    "retrieved_doc_id": hit["doc_id"],
                    "retrieved_title": hit["title"],
                    "retrieved_page_start": hit["page_start"],
                    "retrieved_page_end": hit["page_end"],
                    "section_title": hit["section_title"],
                    "gold_page_hit": str(hit["is_correct"]).lower() == "true",
                    "query_latency_ms": hit["query_latency_ms"],
                    "preview": hit["preview"],
                })

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence = pd.DataFrame(records)
    evidence.to_csv(output, index=False)

    print(f"Saved {len(evidence)} ranked passage records to {output}")
    print("Selected questions:", ", ".join(args.question_ids))
    print("Review preview text and source PDF pages before attributing retrieval behaviour.")


if __name__ == "__main__":
    main()
