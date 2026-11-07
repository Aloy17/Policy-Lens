import argparse
from pathlib import Path

import pandas as pd
import yaml

from src.embedder import Embedder
from src.vector_store import VectorStore


def load_config(config_path: str = "config.yaml") -> dict:
    """Load project configuration."""
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def page_range_matches(
    metadata: dict,
    expected_start: int,
    expected_end: int,
) -> bool:
    """Check whether a retrieved chunk overlaps the expected page range."""
    retrieved_start = int(metadata.get("page_start", 0))
    retrieved_end = int(metadata.get("page_end", 0))

    return (
        retrieved_start <= expected_end
        and retrieved_end >= expected_start
    )


def is_correct_result(
    metadata: dict,
    expected_doc_id: str,
    expected_start: int,
    expected_end: int,
) -> bool:
    """Check whether a retrieved result matches the gold document and pages."""
    if metadata.get("doc_id") != expected_doc_id:
        return False

    return page_range_matches(
        metadata,
        expected_start,
        expected_end,
    )


def evaluate_strategy(
    questions: pd.DataFrame,
    store: VectorStore,
    embedder: Embedder,
    strategy: str,
    top_k: int = 10,
) -> tuple[list[dict], dict]:
    """Evaluate one chunking strategy."""
    logs = []
    reciprocal_ranks = []

    recall_counts = {
        3: 0,
        5: 0,
        10: 0,
    }

    for question_number, row in enumerate(
        questions.to_dict("records"),
        start=1,
    ):
        query = row["question"]

        query_embedding = embedder.embed_texts([query])[0]

        results = store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        expected_doc_id = str(row["expected_doc_id"])
        expected_start = int(row["expected_page_start"])
        expected_end = int(row["expected_page_end"])

        first_correct_rank = None

        for rank, (document, metadata, distance) in enumerate(
            zip(documents, metadatas, distances),
            start=1,
        ):
            correct = is_correct_result(
                metadata,
                expected_doc_id,
                expected_start,
                expected_end,
            )

            if correct and first_correct_rank is None:
                first_correct_rank = rank

            logs.append(
                {
                    "question_id": question_number,
                    "question": query,
                    "strategy": strategy,
                    "rank": rank,
                    "score": round(1 - distance, 4),
                    "doc_id": metadata.get("doc_id", ""),
                    "title": metadata.get("title", ""),
                    "page_start": metadata.get("page_start", ""),
                    "page_end": metadata.get("page_end", ""),
                    "section_title": metadata.get(
                        "section_title",
                        "",
                    ),
                    "is_correct": correct,
                    "is_table_question": row.get(
                        "is_table_question",
                        False,
                    ),
                    "is_paraphrased": row.get(
                        "is_paraphrased",
                        False,
                    ),
                    "preview": " ".join(document.split())[:200],
                }
            )

        if first_correct_rank is not None:
            reciprocal_ranks.append(1 / first_correct_rank)

            if first_correct_rank <= 3:
                recall_counts[3] += 1

            if first_correct_rank <= 5:
                recall_counts[5] += 1

            if first_correct_rank <= 10:
                recall_counts[10] += 1
        else:
            reciprocal_ranks.append(0)

    total_questions = len(questions)

    if total_questions == 0:
        raise ValueError("No evaluation questions found.")

    metrics = {
        "strategy": strategy,
        "questions": total_questions,
        "recall_at_3": recall_counts[3] / total_questions,
        "recall_at_5": recall_counts[5] / total_questions,
        "recall_at_10": recall_counts[10] / total_questions,
        "mrr": sum(reciprocal_ranks) / total_questions,
    }

    return logs, metrics


def calculate_subset_metrics(
    questions: pd.DataFrame,
    logs: list[dict],
    strategy: str,
    column: str,
) -> dict | None:
    """Calculate Recall@3/5/10 and MRR for a question subset."""

    subset = questions[
        questions[column].astype(str).str.lower() == "true"
    ]

    if subset.empty:
        return None

    subset_ids = set(
        subset.index + 1
    )

    strategy_logs = [
        log
        for log in logs
        if log["strategy"] == strategy
        and log["question_id"] in subset_ids
    ]

    reciprocal_ranks = []
    recall_counts = {3: 0, 5: 0, 10: 0}

    for question_id in subset_ids:
        question_logs = [
            log
            for log in strategy_logs
            if log["question_id"] == question_id
        ]

        correct_ranks = [
            log["rank"]
            for log in question_logs
            if log["is_correct"]
        ]

        if correct_ranks:
            first_rank = min(correct_ranks)
            reciprocal_ranks.append(1 / first_rank)

            if first_rank <= 3:
                recall_counts[3] += 1
            if first_rank <= 5:
                recall_counts[5] += 1
            if first_rank <= 10:
                recall_counts[10] += 1
        else:
            reciprocal_ranks.append(0)

    total = len(subset_ids)

    return {
        "strategy": strategy,
        "questions": total,
        "recall_at_3": recall_counts[3] / total,
        "recall_at_5": recall_counts[5] / total,
        "recall_at_10": recall_counts[10] / total,
        "mrr": sum(reciprocal_ranks) / total,
    }


def print_metrics(title: str, metrics: list[dict]) -> None:
    """Print a formatted metrics table."""
    print(f"\n{title}")
    print("=" * 60)

    print(
        pd.DataFrame(metrics)[
            [
                "strategy",
                "questions",
                "recall_at_3",
                "recall_at_5",
                "recall_at_10",
                "mrr",
            ]
        ].to_string(index=False)
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate PolicyLens retrieval."
    )

    parser.add_argument(
        "--questions",
        default="eval/questions.csv",
        help="Path to evaluation questions CSV.",
    )

    parser.add_argument(
        "--collection",
        default="policylens_v1",
        help="Base Chroma collection name.",
    )

    parser.add_argument(
        "--output",
        default="eval/retrieval_log.csv",
        help="Output retrieval log.",
    )

    args = parser.parse_args()

    config = load_config()

    questions = pd.read_csv(args.questions)

    required_columns = {
        "question",
        "expected_doc_id",
        "expected_page_start",
        "expected_page_end",
        "is_table_question",
        "is_paraphrased",
    }

    missing_columns = required_columns - set(questions.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    embedder = Embedder(
        model_name=config["embedding"]["model"],
        batch_size=config["embedding"]["batch_size"],
        normalize_embeddings=config["embedding"]["normalize_embeddings"],
    )

    all_logs = []
    all_metrics = []

    for strategy in ["fixed", "structure"]:
        print(f"\nEvaluating {strategy} strategy...")

        store = VectorStore(
            path=config["vector_store"]["path"],
            collection_name=f"{args.collection}_{strategy}",
        )

        logs, metrics = evaluate_strategy(
            questions=questions,
            store=store,
            embedder=embedder,
            strategy=strategy,
            top_k=10,
        )

        all_logs.extend(logs)
        all_metrics.append(metrics)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(all_logs).to_csv(
        output_path,
        index=False,
    )

    print_metrics(
        "Overall evaluation results",
        all_metrics,
    )

    for column, title in [
        ("is_table_question", "Table-question results"),
        ("is_paraphrased", "Paraphrased-question results"),
    ]:
        subset_metrics = []

        for strategy in ["fixed", "structure"]:
            metrics = calculate_subset_metrics(
                questions=questions,
                logs=all_logs,
                strategy=strategy,
                column=column,
            )

            if metrics is not None:
                subset_metrics.append(metrics)

        if subset_metrics:
            print_metrics(title, subset_metrics)

    print("\nSaved retrieval log:")
    print(output_path)


if __name__ == "__main__":
    main()