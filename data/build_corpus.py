from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

import pymupdf
import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
MANIFEST = DATA_DIR / "manifest.csv"
REPORT = DATA_DIR / "corpus_report.csv"

TARGET_DOCS = 30
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/pdf,*/*",
}

DOCUMENTS = [
    (
        "SEBI",
        "Master Circular for Social Stock Exchange",
        "https://www.sebi.gov.in/sebi_data/attachdocs/jan-2026/1768907353144.pdf",
        "2026-01",
    ),
    (
        "SEBI",
        "Master Circular for Listing Obligations and Disclosure Requirements 2026",
        "https://www.sebi.gov.in/sebi_data/attachdocs/jan-2026/1769776024792.pdf",
        "2026-01-30",
    ),
]


def clean_url(url: str) -> str:
    url = url.strip()

    match = re.fullmatch(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        url,
    )

    return match.group(2) if match else url


def valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1024:
        return False

    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def page_stats(path: Path) -> tuple[int, int, int]:
    with pymupdf.open(path) as doc:
        low_text_pages = 0
        total_words = 0

        for page in doc:
            words = len(page.get_text("text").split())
            total_words += words

            if words < 20:
                low_text_pages += 1

        return len(doc), low_text_pages, total_words


def slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower())
    value = value.strip("_")

    return value[:70] or "document"


def load_existing() -> list[dict]:
    if not MANIFEST.exists():
        return []

    with MANIFEST.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        return list(csv.DictReader(f))


def save_manifest(rows: list[dict]) -> None:
    fields = [
        "doc_id",
        "title",
        "issuer",
        "issue_date",
        "url",
        "page_count",
        "document_type",
    ]

    with MANIFEST.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def download_one(
    session: requests.Session,
    issuer: str,
    title: str,
    source_url: str,
    issue_date: str,
    existing_ids: set[str],
    used_hashes: set[str],
) -> dict | None:
    doc_id = f"{issuer.lower()}_{slug(title)}"
    output_path = PDF_DIR / f"{doc_id}.pdf"

    if doc_id in existing_ids:
        print(f"SKIP | already in manifest | {doc_id}")
        return None

    print(f"DOWNLOAD | {issuer} | {title}")

    url = clean_url(source_url)

    for attempt in range(1, 4):
        try:
            print(f"DOWNLOAD ATTEMPT | {attempt}/3")

            response = session.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")

            if "application/pdf" not in content_type.lower():
                print(
                    f"SKIP | not a PDF | "
                    f"content_type={content_type}"
                )
                return None

            with output_path.open("wb") as f:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        f.write(chunk)

            if valid_pdf(output_path):
                break

            output_path.unlink(missing_ok=True)

            print("RETRY | downloaded file is not a valid PDF")

        except Exception as exc:
            output_path.unlink(missing_ok=True)

            print(
                f"RETRY | {type(exc).__name__}: {exc}"
            )

            if attempt == 3:
                print("SKIP | all download attempts failed")
                return None
    else:
        return None

    file_hash = sha256(output_path)

    if file_hash in used_hashes:
        output_path.unlink(missing_ok=True)
        print("SKIP | duplicate PDF")
        return None

    pages, low_text, words = page_stats(output_path)

    if pages == 0 or words < 30:
        output_path.unlink(missing_ok=True)

        print(
            f"SKIP | unusable PDF | "
            f"pages={pages} words={words}"
        )

        return None

    document_type = (
        "scanned_or_mixed"
        if low_text >= max(2, pages // 10)
        else "text_native"
    )

    print(
        f"OK | pages={pages} | "
        f"words={words} | "
        f"low_text_pages={low_text} | "
        f"type={document_type}"
    )

    used_hashes.add(file_hash)
    existing_ids.add(doc_id)

    return {
        "doc_id": doc_id,
        "title": title,
        "issuer": issuer,
        "issue_date": issue_date,
        "url": url,
        "page_count": str(pages),
        "document_type": document_type,
    }


def build_report(rows: list[dict]) -> None:
    report_rows = []

    for row in rows:
        path = PDF_DIR / f"{row['doc_id']}.pdf"

        if not valid_pdf(path):
            continue

        pages, low_text, words = page_stats(path)

        report_rows.append(
            {
                "doc_id": row["doc_id"],
                "issuer": row["issuer"],
                "title": row["title"],
                "page_count": pages,
                "word_count": words,
                "low_text_pages": low_text,
                "document_type": row["document_type"],
            }
        )

    fields = [
        "doc_id",
        "issuer",
        "title",
        "page_count",
        "word_count",
        "low_text_pages",
        "document_type",
    ]

    with REPORT.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report_rows)


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    existing = load_existing()

    existing_ids = {
        row["doc_id"]
        for row in existing
        if row.get("doc_id")
    }

    used_hashes = set()

    for row in existing:
        path = PDF_DIR / f"{row['doc_id']}.pdf"

        if valid_pdf(path):
            used_hashes.add(sha256(path))

    print(f"EXISTING | {len(existing)} manifest documents")

    rows = list(existing)

    if len(rows) >= TARGET_DOCS:
        print(
            f"TARGET ALREADY MET | documents={len(rows)}"
        )

        build_report(rows)
        return

    session = requests.Session()

    for index, document in enumerate(DOCUMENTS, start=1):
        if len(rows) >= TARGET_DOCS:
            break

        issuer, title, url, issue_date = document

        print(
            f"\nDOWNLOAD {index}/{len(DOCUMENTS)} | "
            f"{issuer} | {title}"
        )

        row = download_one(
            session,
            issuer,
            title,
            url,
            issue_date,
            existing_ids,
            used_hashes,
        )

        if row:
            rows.append(row)

    save_manifest(rows)
    build_report(rows)

    print("\nCORPUS COMPLETE")
    print(f"documents={len(rows)}")

    if rows:
        total_pages = sum(
            int(row["page_count"])
            for row in rows
        )

        long_docs = sum(
            int(row["page_count"]) > 50
            for row in rows
        )

        scanned = sum(
            row["document_type"] == "scanned_or_mixed"
            for row in rows
        )

        print(f"total_pages={total_pages}")
        print(f"long_docs_gt_50_pages={long_docs}")
        print(f"scanned_or_mixed={scanned}")

    if len(rows) < TARGET_DOCS:
        print(
            f"WARNING | only {len(rows)} documents available; "
            f"target is {TARGET_DOCS}"
        )


if __name__ == "__main__":
    main()