import argparse
import json
import os
import platform
import statistics
import time
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
        question_id = str(row.get("id", question_number))
        query = row["question"]

        query_embedding = embedder.embed_texts([query])[0]

        query_started = time.perf_counter()
        results = store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )
        query_latency_ms = (time.perf_counter() - query_started) * 1000

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
                    "question_id": question_id,
                    "question": query,
                    "strategy": strategy,
                    "rank": rank,
                    "score": round(1 - distance, 4),
                    "query_latency_ms": round(query_latency_ms, 3),
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
        subset["id"].astype(str)
    ) if "id" in subset.columns else set(
        str(index + 1) for index in subset.index
    )

    strategy_logs = [
        log
        for log in logs
        if log["strategy"] == strategy
        and str(log["question_id"]) in subset_ids
    ]

    reciprocal_ranks = []
    recall_counts = {3: 0, 5: 0, 10: 0}

    for question_id in subset_ids:
        question_logs = [
            log
            for log in strategy_logs
            if str(log["question_id"]) == str(question_id)
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
        "--manifest",
        default="data/manifest.csv",
        help="Corpus manifest used to validate gold document IDs and page bounds.",
    )

    parser.add_argument(
        "--collection",
        default="policylens_v1",
        help="Base Chroma collection name.",
    )

    parser.add_argument(
        "--db-path",
        default=None,
        help="Chroma database directory. Defaults to vector_store.path in config.yaml.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of retrieved chunks per question (minimum 10).",
    )

    parser.add_argument(
        "--metrics-output",
        default=None,
        help="Metrics CSV path. Defaults beside --output.",
    )

    parser.add_argument(
        "--output",
        default="eval/retrieval_log_phase3.csv",
        help="Output retrieval log (kept separate from historical logs).",
    )

    args = parser.parse_args()

    config = load_config()

    questions = pd.read_csv(args.questions)

    required_columns = {
        "id",
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

    if questions["id"].astype(str).duplicated().any():
        raise ValueError("Question IDs must be unique.")

    if questions[list(required_columns)].isna().any().any():
        raise ValueError("Evaluation questions contain blank required fields.")

    if (questions["expected_page_start"].astype(int) < 1).any():
        raise ValueError("Gold page numbers must be positive and 1-based.")
    if (questions["expected_page_end"].astype(int) < questions["expected_page_start"].astype(int)).any():
        raise ValueError("Gold page end must be >= page start.")

    manifest = pd.read_csv(args.manifest)
    if not {"doc_id", "page_count"}.issubset(manifest.columns):
        raise ValueError("Manifest must contain doc_id and page_count columns.")
    if manifest["doc_id"].astype(str).duplicated().any():
        raise ValueError("Manifest contains duplicate doc_id values.")
    page_counts = dict(zip(
        manifest["doc_id"].astype(str),
        pd.to_numeric(manifest["page_count"], errors="raise").astype(int),
    ))
    for row in questions.to_dict("records"):
        doc_id = str(row["expected_doc_id"])
        if doc_id not in page_counts:
            raise ValueError(f"{row['id']}: gold document {doc_id!r} is absent from manifest.")
        if int(row["expected_page_end"]) > page_counts[doc_id]:
            raise ValueError(
                f"{row['id']}: gold page {row['expected_page_end']} exceeds "
                f"{doc_id} page_count {page_counts[doc_id]}."
            )

    embedder = Embedder(
        model_name=config["embedding"]["model"],
        batch_size=config["embedding"]["batch_size"],
        normalize_embeddings=config["embedding"]["normalize_embeddings"],
    )

    if args.top_k < 10:
        raise ValueError("--top-k must be at least 10 for Recall@10.")

    if len(questions) != 25:
        raise ValueError(f"Expected exactly 25 evaluation questions; found {len(questions)}.")

    for column, expected_count in [("is_table_question", 5), ("is_paraphrased", 5)]:
        actual_count = int(
            questions[column].astype(str).str.lower().eq("true").sum()
        )
        if actual_count != expected_count:
            raise ValueError(
                f"Expected exactly {expected_count} {column} records; found {actual_count}."
            )

    db_path = args.db_path or config["vector_store"]["path"]

    all_logs = []
    all_metrics = []

    for strategy in ["fixed", "structure"]:
        print(f"\nEvaluating {strategy} strategy...")

        store = VectorStore(
            path=db_path,
            collection_name=f"{args.collection}_{strategy}",
        )

        count = store.count()
        if count == 0:
            raise RuntimeError(
                f"Collection '{args.collection}_{strategy}' at '{db_path}' is empty. "
                "Check --db-path and --collection before evaluating."
            )

        print(f"Indexed chunks: {count}")

        logs, metrics = evaluate_strategy(
            questions=questions,
            store=store,
            embedder=embedder,
            strategy=strategy,
            top_k=args.top_k,
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

    metrics_rows = [
        {"subset": "overall", **metrics}
        for metrics in all_metrics
    ]

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
            subset_name = (
                "table_questions"
                if column == "is_table_question"
                else "paraphrased_questions"
            )
            metrics_rows.extend(
                {"subset": subset_name, **metrics}
                for metrics in subset_metrics
            )

    metrics_path = Path(args.metrics_output) if args.metrics_output else output_path.with_name("metrics_phase3.csv")
    pd.DataFrame(metrics_rows).to_csv(metrics_path, index=False)
    print("Saved metrics:")
    print(metrics_path)

    latency_values = [
        row["query_latency_ms"] for row in all_logs if row["rank"] == 1
    ]
    run_metadata = {
        "database_path": str(Path(db_path).expanduser().resolve()),
        "collection_base": args.collection,
        "collection_counts": {
            strategy: VectorStore(
                path=db_path,
                collection_name=f"{args.collection}_{strategy}",
            ).count()
            for strategy in ["fixed", "structure"]
        },
        "embedding_model": config["embedding"]["model"],
        "embedding_batch_size": config["embedding"]["batch_size"],
        "normalized_embeddings": config["embedding"]["normalize_embeddings"],
        "top_k": args.top_k,
        "question_count": len(questions),
        "table_question_count": int(questions["is_table_question"].astype(str).str.lower().eq("true").sum()),
        "paraphrased_question_count": int(questions["is_paraphrased"].astype(str).str.lower().eq("true").sum()),
        "mean_query_latency_ms": round(statistics.mean(latency_values), 3) if latency_values else None,
        "median_query_latency_ms": round(statistics.median(latency_values), 3) if latency_values else None,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "embedding_api_cost": 0,
        "embedding_api_cost_currency": "USD",
        "embedding_cost_note": "Local Sentence Transformers inference; no hosted embedding API charge.",
    }
    metadata_path = output_path.with_name("run_metadata_phase3.json")
    metadata_path.write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")
    print("\nSaved run metadata:")
    print(metadata_path)

    print("\nSaved retrieval log:")
    print(output_path)


if __name__ == "__main__":
    main()