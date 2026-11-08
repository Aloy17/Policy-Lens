"""Export every gold-referenced local PDF page for one consolidated audit."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import pymupdf

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default="eval/questions.csv")
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--pdf-dir", required=True)
    parser.add_argument("--output-dir", default="eval/gold_page_audit")
    args = parser.parse_args()

    questions = pd.read_csv(args.questions).fillna("")
    manifest = pd.read_csv(args.manifest).fillna("")
    required_q = {"id", "question", "expected_doc_id", "expected_page_start", "expected_page_end"}
    required_m = {"doc_id", "title", "page_count"}
    if not required_q.issubset(questions.columns):
        raise SystemExit(f"Questions CSV missing columns: {sorted(required_q - set(questions.columns))}")
    if not required_m.issubset(manifest.columns):
        raise SystemExit(f"Manifest missing columns: {sorted(required_m - set(manifest.columns))}")
    if questions["id"].duplicated().any():
        raise SystemExit("Duplicate question IDs found.")
    manifest_by_id = manifest.set_index("doc_id").to_dict("index")
    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pages_by_doc: dict[str, set[int]] = {}
    for row in questions.to_dict("records"):
        doc_id = str(row["expected_doc_id"])
        if doc_id not in manifest_by_id:
            raise SystemExit(f"{row['id']}: document {doc_id} is absent from manifest.")
        start, end = int(row["expected_page_start"]), int(row["expected_page_end"])
        declared = int(manifest_by_id[doc_id]["page_count"])
        if start < 1 or end < start or end > declared:
            raise SystemExit(f"{row['id']}: invalid range {start}-{end} for manifest page count {declared}.")
        pages_by_doc.setdefault(doc_id, set()).update(range(start, end + 1))

    report = [
        "# PolicyLens gold-set local PDF page audit", "",
        f"- Questions: {len(questions)}",
        f"- Unique referenced PDF pages: {sum(len(p) for p in pages_by_doc.values())}",
        f"- Source PDF directory: {pdf_dir}", "",
        "PDF page numbers are 1-based and refer to the exact local files used for this audit.",
        "Compare each question's answer-bearing passage with the rendered page in gold_pages_review.pdf. Check table row/column alignment and footnotes visually, not from extracted text alone.", ""
    ]
    review_pdf = pymupdf.open()
    for doc_id, page_numbers in pages_by_doc.items():
        source_path = pdf_dir / f"{doc_id}.pdf"
        if not source_path.is_file():
            raise SystemExit(f"PDF not found: {source_path}")
        meta = manifest_by_id[doc_id]
        with pymupdf.open(source_path) as source:
            report.extend(["---", "", f"## {doc_id} — {meta.get('title', '')}", "",
                           f"- Actual PDF pages: {len(source)}",
                           f"- Manifest pages: {meta['page_count']}", ""])
            for page_no in sorted(page_numbers):
                if page_no > len(source):
                    raise SystemExit(f"{doc_id}: requested page {page_no}, but local PDF has {len(source)} pages.")
                page = source[page_no - 1]
                report.extend([f"### PDF page {page_no}", "",
                               page.get_text("text").strip() or "[NO NATIVE TEXT — visual inspection required]", ""])
                review_pdf.insert_pdf(source, from_page=page_no - 1, to_page=page_no - 1)
                review_pdf[-1].insert_text((24, 24), f"{doc_id} | PDF page {page_no}",
                                           fontsize=8, color=(0.8, 0.1, 0.1), overlay=True)

    report_path = output_dir / "gold_pages_text.md"
    pdf_path = output_dir / "gold_pages_review.pdf"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    review_pdf.save(pdf_path, garbage=4, deflate=True)
    review_pdf.close()
    print(f"Questions: {len(questions)}")
    print(f"Unique referenced pages: {sum(len(p) for p in pages_by_doc.values())}")
    print(f"Text bundle: {report_path}")
    print(f"Visual PDF bundle: {pdf_path}")
    print("Source PDFs, questions.csv, and manifest.csv were not modified.")

if __name__ == "__main__":
    main()
