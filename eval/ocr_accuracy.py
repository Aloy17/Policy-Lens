"""Estimate OCR word accuracy for scanned pages against a hand-checked reference.

Each reference file in eval/ocr_reference/ is named <doc_id>_p<page>.txt and holds the
body text of that PDF page (margin notes, running heads and page numbers excluded).
The page is OCR'd the same way the ingestion pipeline does it (src.ocr.ocr_page).

Metrics (word level, case-sensitive, after whitespace tokenisation):
  - WER: word error rate from edit distance against the reference body text.
  - word_accuracy: 1 - WER, floored at 0.
  - word_recall: share of reference words found anywhere in the OCR text (order ignored),
    which is not hurt by extra OCR words from margin notes or running heads.

Usage:
    PYTHONPATH=. python eval/ocr_accuracy.py --output eval/ocr_accuracy.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


def tokenize(text: str) -> list[str]:
    return text.split()


def edit_distance(ref: list[str], hyp: list[str]) -> int:
    previous = list(range(len(hyp) + 1))
    for i, ref_word in enumerate(ref, start=1):
        current = [i]
        for j, hyp_word in enumerate(hyp, start=1):
            cost = 0 if ref_word == hyp_word else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def score(reference: str, ocr_text: str) -> dict[str, float]:
    ref, hyp = tokenize(reference), tokenize(ocr_text)
    errors = edit_distance(ref, hyp)
    wer = errors / len(ref) if ref else 0.0
    ref_counts, hyp_counts = Counter(ref), Counter(hyp)
    matched = sum(min(count, hyp_counts[word]) for word, count in ref_counts.items())
    return {
        "reference_words": len(ref),
        "ocr_words": len(hyp),
        "word_errors": errors,
        "wer": round(wer, 4),
        "word_accuracy": round(max(0.0, 1 - wer), 4),
        "word_recall": round(matched / len(ref), 4) if ref else 0.0,
    }


def main() -> None:
    from src.ocr import ocr_page

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reference-dir", default="eval/ocr_reference")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--language", default="eng")
    parser.add_argument("--output", default="eval/ocr_accuracy.csv")
    args = parser.parse_args()

    rows = []
    for ref_path in sorted(Path(args.reference_dir).glob("*.txt")):
        match = re.fullmatch(r"(?P<doc>.+)_p(?P<page>\d+)", ref_path.stem)
        if not match:
            continue
        doc_id, page = match.group("doc"), int(match.group("page"))
        pdf_path = Path(args.pdf_dir) / f"{doc_id}.pdf"
        ocr_text = ocr_page(pdf_path, page, args.language)
        result = score(ref_path.read_text(encoding="utf-8"), ocr_text)
        rows.append({"doc_id": doc_id, "page": page, **result})
        print(rows[-1])

    if not rows:
        raise SystemExit("No reference files found.")
    with open(args.output, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    total_ref = sum(r["reference_words"] for r in rows)
    weighted = sum(r["word_accuracy"] * r["reference_words"] for r in rows) / total_ref
    print(f"Pages: {len(rows)} | weighted word accuracy: {weighted:.4f}")


if __name__ == "__main__":
    main()
