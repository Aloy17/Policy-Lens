"""Task 1 retrieval benchmark: fixed-size vs structure-aware chunking.

Runs the v2 gold questions against `<base>_fixed` and `<base>_structure` with
identical query embeddings, top-k and retrieval call, and writes a dated output
directory. The Chroma database is never written to: by default it is copied to a
temporary directory and only the copy is opened; the original tree is hashed
before and after the run and the result is recorded in run_metadata.json.

    PYTHONPATH=. python eval/run_retrieval_benchmark.py \
        --db-path "<path to chroma_db>" --collection-base policylens_v1

Metric definitions live in eval/retrieval_metrics.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import random
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieval_metrics import (  # noqa: E402
    DEFAULT_KS, Passage, aggregate, is_relevant, matches_passage, parse_passages, result_page_range, score_question,
)

SCRIPT_VERSION = "1.0.0"
DATASET_VERSION = "gold_v2_2026-11-14"
STRATEGIES = ("fixed", "structure")
EXPECTED_COUNTS = {"fixed": 5932, "structure": 15773}  # from the Task 1 brief; mismatch is warned, not fatal
PREVIEW_CHARS = 200


class Searcher(Protocol):
    def count(self) -> int: ...
    def query(self, embedding: Sequence[float], top_k: int) -> dict[str, Any]: ...


class ChromaSearcher:
    """Read-only wrapper: get_collection (never create) and query."""

    def __init__(self, client, name: str) -> None:
        self.collection = client.get_collection(name)

    def count(self) -> int:
        return self.collection.count()

    def query(self, embedding, top_k):
        return self.collection.query(
            query_embeddings=[list(embedding)], n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )


def load_questions(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["_passages"] = parse_passages(row["gold_passages"])
        row["_v1_passage"] = Passage(
            row["expected_doc_id"], int(row["expected_page_start"]), int(row["expected_page_end"])
        )
        row["_categories"] = set(filter(None, row["categories"].split("|")))
    return rows


def evidence_passages_for_result(
    document: str | None, metadata: dict | None, passages: Sequence[Passage],
    term_groups: Sequence[str],
) -> set[int]:
    """Return only passages whose page range overlaps and whose terms occur in this chunk."""
    if not isinstance(document, str) or not document.strip():
        return set()
    text = " ".join(document.lower().split())
    matched = set()
    for index, (gold, group) in enumerate(zip(passages, term_groups)):
        if not matches_passage(metadata, gold):
            continue
        terms = [term.strip().lower() for term in group.split("|") if term.strip()]
        if terms and all(" ".join(term.split()) in text for term in terms):
            matched.add(index)
    return matched


def score_evidence_term_proxy(
    documents: Sequence[str | None], metadatas: Sequence[dict | None],
    passages: Sequence[Passage], term_groups: Sequence[str], ks=DEFAULT_KS,
) -> dict:
    """Score passage-term lexical matches; this is not semantic answer validation."""
    if len(documents) != len(metadatas):
        raise ValueError("Evidence scoring requires aligned documents and metadata.")
    if len(passages) != len(term_groups):
        raise ValueError("Each gold passage must have one passage_terms group.")
    if not passages:
        raise ValueError("At least one gold passage is required.")
    ks = tuple(ks)
    if any(k < 1 for k in ks):
        raise ValueError("k must be >= 1.")
    covered_at_rank = [
        evidence_passages_for_result(doc, meta, passages, term_groups)
        for doc, meta in zip(documents, metadatas)
    ]
    flags = [bool(hits) for hits in covered_at_rank]
    first_rank = next((rank for rank, hit in enumerate(flags, 1) if hit), None)
    malformed = sum(result_page_range(meta) is None for meta in metadatas)
    scores = {
        "first_relevant_rank": first_rank, "rr": 1.0 / first_rank if first_rank else 0.0,
        "retrieved": len(flags), "malformed_results": malformed, "relevant_flags": flags,
    }
    for k in ks:
        covered = set().union(*covered_at_rank[:k]) if covered_at_rank[:k] else set()
        scores[f"hit@{k}"] = float(any(flags[:k]))
        scores[f"recall@{k}"] = len(covered) / len(passages)
        scores[f"precision@{k}"] = sum(flags[:k]) / k
    return scores

def run_benchmark(
    questions: list[dict],
    query_embeddings: dict[str, Sequence[float]],
    searchers: dict[str, Searcher],
    top_k: int = 10,
) -> tuple[list[dict], dict[str, dict[str, dict]]]:
    """Return (retrieval log rows, per-strategy per-question scores)."""
    if top_k < max(DEFAULT_KS):
        raise ValueError(f"top_k must be >= {max(DEFAULT_KS)} for Recall@{max(DEFAULT_KS)}.")
    log: list[dict] = []
    scores: dict[str, dict[str, dict]] = {s: {} for s in searchers}
    for strategy, searcher in searchers.items():
        for q in questions:
            raw = searcher.query(query_embeddings[q["id"]], top_k)
            if not isinstance(raw, dict):
                raise TypeError(f"{strategy}/{q['id']}: Chroma query must return a dictionary.")
            arrays = {}
            for field in ("ids", "documents", "metadatas", "distances"):
                value = raw.get(field)
                if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], list):
                    raise ValueError(
                        f"{strategy}/{q['id']}: expected one result list for {field}; "
                        f"got {type(value).__name__}."
                    )
                arrays[field] = value[0]
            ids, docs, metas, dists = (
                arrays["ids"], arrays["documents"], arrays["metadatas"], arrays["distances"]
            )
            lengths = {name: len(value) for name, value in arrays.items()}
            if len(set(lengths.values())) != 1:
                raise ValueError(f"{strategy}/{q['id']}: inconsistent Chroma result lengths: {lengths}")
            scores[strategy][q["id"]] = score_question(metas, q["_passages"])
            term_groups = q["passage_terms"].split(";")
            # This is a lexical evidence proxy, not semantic/answer correctness.
            scores[strategy][q["id"]]["evidence_term_proxy"] = score_evidence_term_proxy(
                docs, metas, q["_passages"], term_groups
            )
            v1_scores = score_question(metas, [q["_v1_passage"]])
            scores[strategy][q["id"]]["v1"] = v1_scores
            for rank, cid in enumerate(ids, 1):
                doc, meta, dist = docs[rank - 1], metas[rank - 1], dists[rank - 1]
                meta = meta if isinstance(meta, dict) else {}
                parsed = result_page_range(meta)
                matched = [i for i, p in enumerate(q["_passages"]) if is_relevant(meta, [p])]
                notes = []
                if parsed is None:
                    notes.append("malformed_metadata")
                log.append({
                    "question_id": q["id"], "question": q["question"], "strategy": strategy, "rank": rank,
                    "doc_id": meta.get("doc_id", ""), "chunk_id": cid,
                    "page_start": meta.get("page_start", ""), "page_end": meta.get("page_end", ""),
                    "section_title": meta.get("section_title", ""),
                    "distance": round(float(dist), 6), "similarity": round(1.0 - float(dist), 6),
                    "is_relevant": bool(matched),
                    "evidence_term_proxy_relevant": bool(
                        evidence_passages_for_result(doc, meta, q["_passages"], term_groups)
                    ),
                    "matched_gold_passages": ";".join(str(i + 1) for i in matched),
                    "expected_doc_id": q["_passages"][0].doc_id,
                    "expected_passages": q["gold_passages"],
                    "v1_expected_pages": f"{q['expected_page_start']}-{q['expected_page_end']}",
                    "label_status": q["label_status"], "notes": ";".join(notes),
                    "preview": " ".join((doc or "").split())[:PREVIEW_CHARS],
                })
    return log, scores


def subset(questions: list[dict], predicate) -> list[str]:
    return [q["id"] for q in questions if predicate(q)]


def metrics_tables(questions: list[dict], scores: dict[str, dict[str, dict]]) -> list[dict]:
    headline = [q for q in questions if q["include_in_headline"].lower() == "true"]
    groups: dict[str, list[str]] = {"headline_all_valid": [q["id"] for q in headline]}
    for cat in ("direct", "paraphrase", "table", "numeric_date", "clause", "distinction", "multi_passage"):
        groups[f"category_{cat}"] = subset(headline, lambda q, c=cat: c in q["_categories"])
    groups["original_q01_q25_v2_labels"] = subset(headline, lambda q: q["id"].startswith("q") and int(q["id"][1:]) <= 25)
    groups["new_q26_q37"] = subset(headline, lambda q: q["id"].startswith("q") and int(q["id"][1:]) >= 26)
    groups["extension_x01_x04"] = subset(headline, lambda q: q["id"].startswith("x"))
    rows = []
    for name, ids in groups.items():
        if not ids:
            continue
        for strategy in scores:
            agg = aggregate([scores[strategy][i] for i in ids])
            rows.append({"subset": name, "relevance_basis": "page_overlap_proxy", "strategy": strategy, **agg})
            evidence_agg = aggregate([scores[strategy][i]["evidence_term_proxy"] for i in ids])
            rows.append({"subset": name, "relevance_basis": "passage_term_lexical_proxy", "strategy": strategy, **evidence_agg})
    # Legacy-comparable view: original 25 questions, original v1 single-range labels.
    ids = groups["original_q01_q25_v2_labels"]
    for strategy in scores:
        agg = aggregate([scores[strategy][i]["v1"] for i in ids])
        rows.append({"subset": "original_q01_q25_v1_labels", "strategy": strategy, **agg})
    return rows


def per_question_table(questions: list[dict], scores: dict[str, dict[str, dict]]) -> list[dict]:
    rows = []
    for q in questions:
        row: dict[str, Any] = {
            "question_id": q["id"], "label_status": q["label_status"], "categories": q["categories"],
            "gold_passages": q["gold_passages"],
        }
        for s in scores:
            sc = scores[s][q["id"]]
            row[f"{s}_first_relevant_rank"] = sc["first_relevant_rank"] or ""
            for k in DEFAULT_KS:
                row[f"{s}_page_overlap_hit@{k}"] = int(sc[f"hit@{k}"])
                row[f"{s}_page_overlap_recall@{k}"] = round(sc[f"recall@{k}"], 4)
                row[f"{s}_page_overlap_precision@{k}"] = round(sc[f"precision@{k}"], 4)
                ev = sc["evidence_term_proxy"]
                row[f"{s}_evidence_term_hit@{k}"] = int(ev[f"hit@{k}"])
                row[f"{s}_evidence_term_recall@{k}"] = round(ev[f"recall@{k}"], 4)
                row[f"{s}_evidence_term_precision@{k}"] = round(ev[f"precision@{k}"], 4)
        f_rank = scores["fixed"][q["id"]]["first_relevant_rank"]
        s_rank = scores["structure"][q["id"]]["first_relevant_rank"]
        hit_f, hit_s = f_rank is not None, s_rank is not None
        row["outcome_top10"] = (
            "both_hit" if hit_f and hit_s else "only_fixed" if hit_f else "only_structure" if hit_s else "neither"
        )
        row["poorly_ranked"] = ";".join(
            s for s, r in (("fixed", f_rank), ("structure", s_rank)) if r is not None and r > 3
        )
        rows.append(row)
    return rows


def paired_bootstrap(questions, scores, key: str, iterations: int = 10000, seed: int = 0) -> dict:
    """Paired bootstrap of (structure - fixed) mean difference over headline questions."""
    if iterations < 1:
        raise ValueError("iterations must be >= 1.")
    ids = [q["id"] for q in questions if q["include_in_headline"].lower() == "true"]
    if not ids:
        raise ValueError("No headline questions available for paired bootstrap.")
    diffs = [scores["structure"][i][key] - scores["fixed"][i][key] for i in ids]
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(iterations))
    return {
        "metric": key, "questions": len(diffs), "mean_diff_structure_minus_fixed": sum(diffs) / len(diffs),
        "ci95_low": means[int(0.025 * iterations)], "ci95_high": means[int(0.975 * iterations) - 1],
        "questions_structure_better": sum(d > 0 for d in diffs), "questions_fixed_better": sum(d < 0 for d in diffs),
        "questions_tied": sum(d == 0 for d in diffs), "iterations": iterations, "seed": seed,
    }


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_info(repo: Path) -> dict:
    def run(*args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False).stdout.strip()
    return {"commit_sha": run("rev-parse", "HEAD"), "dirty_worktree": bool(run("status", "--porcelain"))}


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_inspection_cases(path: Path, questions, per_q, log) -> None:
    """Auto-select representative cases (with top-3 previews) for manual review."""
    by_id = {q["id"]: q for q in questions}
    picks: list[tuple[str, str]] = []
    def first(pred, label, n=3):
        for r in per_q:
            if pred(r) and len([1 for p in picks if p[0] == label]) < n and r["label_status"] != "invalid":
                picks.append((label, r["question_id"]))
    first(lambda r: r["outcome_top10"] == "both_hit" and not r["poorly_ranked"], "Both succeed (rank<=3)")
    first(lambda r: r["outcome_top10"] == "only_fixed", "Only fixed-size succeeds", 99)
    first(lambda r: r["outcome_top10"] == "only_structure", "Only structure-aware succeeds", 99)
    first(lambda r: r["outcome_top10"] == "neither", "Both fail", 99)
    first(lambda r: bool(r["poorly_ranked"]) and r["outcome_top10"] != "neither", "Relevant but ranked below 3", 99)
    first(lambda r: "table" in r["categories"], "Table-dependent", 99)
    first(lambda r: "paraphrase" in r["categories"], "Paraphrased", 99)
    lines = ["# Cases selected for manual inspection", "",
             "Auto-selected from the run; the written diagnosis belongs in qualitative_error_analysis.md after reading full chunk text and the source PDF page.", ""]
    for label, qid in picks:
        q = by_id[qid]
        lines += [f"## {label}: {qid}", f"Question: {q['question']}", f"Gold passages: `{q['gold_passages']}`", ""]
        for s in STRATEGIES:
            lines.append(f"**{s}**")
            for r in [x for x in log if x["question_id"] == qid and x["strategy"] == s][:3]:
                mark = "RELEVANT" if r["is_relevant"] else "not relevant"
                lines.append(f"- rank {r['rank']} {r['doc_id']} p{r['page_start']}-{r['page_end']} sim={r['similarity']} [{mark}] {r['chunk_id']}: {r['preview']}")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--collection-base", default="policylens_v1")
    parser.add_argument("--questions", default="eval/benchmark_2026-11-14/gold_questions_v2.csv")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--output-dir", default=None, help="Default: eval/benchmark_<UTC date>_run")
    parser.add_argument("--no-copy", action="store_true", help="Open the database in place instead of a temporary copy (not recommended).")
    args = parser.parse_args()

    import chromadb
    import yaml
    from src.embedder import Embedder

    repo = Path(__file__).resolve().parents[1]
    started = datetime.now(timezone.utc)
    out_dir = Path(args.output_dir) if args.output_dir else repo / "eval" / f"benchmark_{started:%Y-%m-%d}_run"
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to overwrite non-empty output directory: {out_dir}")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    questions = load_questions(Path(args.questions))
    db_path = Path(args.db_path).expanduser().resolve()
    hash_before = tree_hash(db_path)

    work_path, tmp = db_path, None
    if not args.no_copy:
        tmp = tempfile.TemporaryDirectory()
        work_path = Path(tmp.name) / "chroma_copy"
        shutil.copytree(db_path, work_path)
    try:
        client = chromadb.PersistentClient(path=str(work_path))
        searchers = {s: ChromaSearcher(client, f"{args.collection_base}_{s}") for s in STRATEGIES}
        counts = {s: searchers[s].count() for s in STRATEGIES}
        warnings = [f"{s}: record count {counts[s]} != expected {EXPECTED_COUNTS[s]}" for s in STRATEGIES if counts[s] != EXPECTED_COUNTS[s]]

        emb_cfg = config["embedding"]
        embedder = Embedder(emb_cfg["model"], emb_cfg["batch_size"], emb_cfg["normalize_embeddings"])
        vectors = embedder.embed_texts([q["question"] for q in questions])
        query_embeddings = {q["id"]: v for q, v in zip(questions, vectors)}

        log, scores = run_benchmark(questions, query_embeddings, searchers, args.top_k)
    finally:
        if tmp:
            tmp.cleanup()
    hash_after = tree_hash(db_path)

    metrics = metrics_tables(questions, scores)
    per_q = per_question_table(questions, scores)
    boot = [paired_bootstrap(questions, scores, key) for key in ("rr", "hit@10", "recall@10", "precision@5")]

    write_csv(out_dir / "retrieval_log.csv", log)
    write_csv(out_dir / "metrics.csv", metrics)
    write_csv(out_dir / "per_question.csv", per_q)
    (out_dir / "paired_bootstrap.json").write_text(json.dumps(boot, indent=2), encoding="utf-8")
    write_inspection_cases(out_dir / "cases_for_inspection.md", questions, per_q, log)

    import chromadb as _c
    import sentence_transformers as _st
    metadata = {
        "evaluation_timestamp_utc": started.isoformat(), "script": "eval/run_retrieval_benchmark.py", "script_version": SCRIPT_VERSION,
        "dataset_version": DATASET_VERSION, "dataset_file": args.questions, "dataset_sha256": sha256_file(Path(args.questions)),
        "question_count": len(questions), "headline_question_count": sum(q["include_in_headline"].lower() == "true" for q in questions),
        **git_info(repo), "collections": {f"{args.collection_base}_{s}": counts[s] for s in STRATEGIES}, "count_warnings": warnings,
        "embedding_model": emb_cfg["model"], "embedding_batch_size": emb_cfg["batch_size"], "normalize_embeddings": emb_cfg["normalize_embeddings"],
        "retrieval": {"top_k": args.top_k, "where_filter": None, "distance_space": "cosine",
                      "distance_meaning": "Chroma cosine distance = 1 - cosine similarity; lower is closer.",
                      "similarity_meaning": "1 - distance; for normalised embeddings this is cosine similarity."},
        "query_embeddings_shared_across_strategies": True,
        "database_path": str(db_path), "opened_from_temporary_copy": not args.no_copy,
        "database_tree_sha256_before": hash_before, "database_tree_sha256_after": hash_after,
        "database_unmodified": hash_before == hash_after,
        "python": platform.python_version(), "chromadb": _c.__version__, "sentence_transformers": _st.__version__, "platform": platform.platform(),
        "malformed_result_count": {s: sum(1 for r in log if r["strategy"] == s and "malformed_metadata" in r["notes"]) for s in STRATEGIES},
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Wrote results to {out_dir}")
    for w in warnings:
        print("WARNING:", w)
    print("database_unmodified:", metadata["database_unmodified"])
    return 0 if metadata["database_unmodified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
