"""Retrieval metrics for the Policy-Lens evaluation.

Pure functions with no Chroma or model dependency, so they can be unit tested
with controlled fixtures.

Relevance
---------
A gold *passage* is (doc_id, page_start, page_end) with an inclusive, 1-based
PDF page range. A retrieved result is relevant to a passage when its metadata
doc_id equals the passage doc_id and its inclusive page range overlaps the
passage range. A result is relevant to a question when it is relevant to at
least one of the question's gold passages.

Metrics (per question, then averaged)
-------------------------------------
- hit_rate@k   1 if any of the top k results is relevant, else 0.
               (The legacy evaluate.py called this "recall@k".)
- recall@k     fraction of the question's gold passages covered by at least one
               relevant result in the top k. Equals hit_rate@k for
               single-passage questions.
- precision@k  relevant results in the top k divided by k. The denominator is k
               even when fewer than k results come back.
- rr           1 / rank of the first relevant result, 0 if none is retrieved.

Malformed results (missing/non-integer page fields, missing doc_id, inverted
page range) are never relevant. In lenient mode they are counted and reported;
in strict mode they raise MalformedMetadataError.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

DEFAULT_KS = (3, 5, 10)


class MalformedMetadataError(ValueError):
    """Raised in strict mode when a retrieved result has unusable metadata."""


@dataclass(frozen=True)
class Passage:
    doc_id: str
    page_start: int
    page_end: int

    def __post_init__(self) -> None:
        if not self.doc_id:
            raise ValueError("Passage doc_id must be non-empty.")
        if self.page_start < 1 or self.page_end < self.page_start:
            raise ValueError(
                f"Invalid inclusive page range {self.page_start}-{self.page_end}."
            )


def parse_passages(spec: str) -> list[Passage]:
    """Parse 'doc_id:start-end;doc_id:start-end' into Passage objects."""
    passages = []
    for part in (spec or "").split(";"):
        part = part.strip()
        if not part:
            continue
        try:
            doc_id, pages = part.rsplit(":", 1)
            start, end = pages.split("-", 1)
            passages.append(Passage(doc_id.strip(), int(start), int(end)))
        except ValueError as error:
            raise ValueError(f"Malformed passage spec: {part!r}") from error
    if not passages:
        raise ValueError("At least one gold passage is required.")
    return passages


def _page_value(metadata: dict, key: str):
    value = metadata.get(key)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def result_page_range(metadata: dict | None):
    """Return (doc_id, start, end) or None when the metadata is unusable."""
    if not isinstance(metadata, dict):
        return None
    doc_id = metadata.get("doc_id")
    start = _page_value(metadata, "page_start")
    end = _page_value(metadata, "page_end")
    if not isinstance(doc_id, str) or not doc_id:
        return None
    if start is None or end is None or start < 1 or end < start:
        return None
    return doc_id, start, end


def matches_passage(metadata: dict | None, passage: Passage, strict: bool = False) -> bool:
    parsed = result_page_range(metadata)
    if parsed is None:
        if strict:
            raise MalformedMetadataError(f"Unusable retrieval metadata: {metadata!r}")
        return False
    doc_id, start, end = parsed
    return (
        doc_id == passage.doc_id
        and start <= passage.page_end
        and end >= passage.page_start
    )


def is_relevant(metadata: dict | None, passages: Sequence[Passage], strict: bool = False) -> bool:
    return any(matches_passage(metadata, p, strict) for p in passages)


def score_question(
    result_metadatas: Sequence[dict | None],
    passages: Sequence[Passage],
    ks: Iterable[int] = DEFAULT_KS,
    strict: bool = False,
) -> dict:
    """Score one question's ranked results (rank 1 first)."""
    ks = tuple(ks)
    if not passages:
        raise ValueError("At least one gold passage is required.")
    if any(k < 1 for k in ks):
        raise ValueError("k must be >= 1.")

    relevant_flags = []
    covered_at_rank: list[set[int]] = []
    malformed = 0
    for metadata in result_metadatas:
        if result_page_range(metadata) is None:
            malformed += 1
            if strict:
                raise MalformedMetadataError(f"Unusable retrieval metadata: {metadata!r}")
        hits = {i for i, p in enumerate(passages) if matches_passage(metadata, p)}
        relevant_flags.append(bool(hits))
        covered_at_rank.append(hits)

    first_rank = next((rank for rank, flag in enumerate(relevant_flags, 1) if flag), None)
    scores = {
        "first_relevant_rank": first_rank,
        "rr": 1.0 / first_rank if first_rank else 0.0,
        "retrieved": len(relevant_flags),
        "malformed_results": malformed,
        "relevant_flags": relevant_flags,
    }
    for k in ks:
        top = relevant_flags[:k]
        covered = set().union(*covered_at_rank[:k]) if covered_at_rank[:k] else set()
        scores[f"hit@{k}"] = 1.0 if any(top) else 0.0
        scores[f"recall@{k}"] = len(covered) / len(passages)
        scores[f"precision@{k}"] = sum(top) / k
    return scores


def aggregate(per_question: Sequence[dict], ks: Iterable[int] = DEFAULT_KS) -> dict:
    """Mean of per-question scores. Raises on an empty set."""
    if not per_question:
        raise ValueError("No questions to aggregate.")
    n = len(per_question)
    out = {"questions": n, "mrr": sum(q["rr"] for q in per_question) / n}
    for k in tuple(ks):
        for name in ("hit", "recall", "precision"):
            key = f"{name}@{k}"
            out[key] = sum(q[key] for q in per_question) / n
    out["malformed_results"] = sum(q["malformed_results"] for q in per_question)
    out["empty_result_questions"] = sum(1 for q in per_question if q["retrieved"] == 0)
    return out
