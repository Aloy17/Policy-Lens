"""Download the corpus PDFs listed in data/manifest.csv into data/pdfs/.

The PDFs are not stored in the repository. Each file is fetched from its
manifest URL and saved as data/pdfs/<doc_id>.pdf. After download the SHA-256
is compared with data/pdf_checksums.csv, which records the files used for the
evaluation. A mismatch means the publisher changed the file since the
evaluation; ingestion still works, but gold page labels may no longer line up.

Usage:
    python data/fetch_pdfs.py
    python data/fetch_pdfs.py --only rbi_kyc_2024 --only rbi_digital_lending_2022
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
MANIFEST = DATA_DIR / "manifest.csv"
CHECKSUMS = DATA_DIR / "pdf_checksums.csv"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/pdf,*/*"}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False


def load_checksums() -> dict[str, str]:
    if not CHECKSUMS.exists():
        return {}
    with CHECKSUMS.open("r", encoding="utf-8", newline="") as handle:
        return {row["doc_id"]: row["sha256"] for row in csv.DictReader(handle)}


def download(session: requests.Session, url: str, target: Path, retries: int = 3) -> bool:
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, headers=HEADERS, timeout=120, allow_redirects=True)
            response.raise_for_status()
            tmp = target.with_suffix(".part")
            tmp.write_bytes(response.content)
            if not is_pdf(tmp):
                tmp.unlink(missing_ok=True)
                raise ValueError("response is not a PDF")
            tmp.replace(target)
            return True
        except Exception as error:  # noqa: BLE001 - report and retry
            print(f"  attempt {attempt}/{retries} failed: {error}")
            time.sleep(2 * attempt)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", action="append", default=None,
                        help="Fetch only this doc_id (repeatable).")
    parser.add_argument("--force", action="store_true",
                        help="Re-download files that already exist and look valid.")
    args = parser.parse_args()

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    checksums = load_checksums()
    with MANIFEST.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    session = requests.Session()
    counts = {"downloaded": 0, "present": 0, "failed": 0, "checksum_mismatch": 0}
    for row in rows:
        doc_id = row["doc_id"]
        if args.only and doc_id not in args.only:
            continue
        target = PDF_DIR / f"{doc_id}.pdf"
        if target.exists() and is_pdf(target) and not args.force:
            counts["present"] += 1
        else:
            print(f"DOWNLOAD | {doc_id}")
            if download(session, row["url"], target):
                counts["downloaded"] += 1
            else:
                counts["failed"] += 1
                print(f"FAILED   | {doc_id} | {row['url']}")
                continue
        expected = checksums.get(doc_id)
        if expected and sha256_of(target) != expected:
            counts["checksum_mismatch"] += 1
            print(f"CHECKSUM | {doc_id} differs from the evaluated file")

    print(counts)
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
