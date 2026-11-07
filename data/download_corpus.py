from pathlib import Path
import csv
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


PDF_DIR = Path(__file__).parent / "pdfs"
MANIFEST = Path(__file__).parent / "manifest.csv"

PDF_DIR.mkdir(parents=True, exist_ok=True)


def clean_url(url: str) -> str:
    """Remove accidental Markdown link formatting."""
    url = url.strip()

    match = re.fullmatch(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        url,
    )

    if match:
        return match.group(2)

    return url


def is_valid_pdf(path: Path) -> bool:
    if not path.exists():
        return False

    try:
        with path.open("rb") as file:
            return file.read(5) == b"%PDF-"
    except OSError:
        return False


def find_pdf_url(session: requests.Session, url: str) -> str:
    """
    Accept either:
    - a direct PDF URL
    - an RBI HTML document page containing a PDF link
    """

    url = clean_url(url)

    if url.lower().split("?")[0].endswith(".pdf"):
        return url

    response = session.get(
        url,
        timeout=120,
        allow_redirects=True,
    )
    response.raise_for_status()

    if response.content.startswith(b"%PDF-"):
        return response.url

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    candidates = []

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if href.lower().endswith(".pdf"):
            candidates.append(
                urljoin(response.url, href)
            )

    if candidates:
        return candidates[0]

    raise ValueError(
        f"No PDF link found on page: {url}"
    )


def download_pdf(
    session: requests.Session,
    document: dict,
) -> str:

    doc_id = document["doc_id"]
    source_url = clean_url(document["url"])
    output_path = PDF_DIR / f"{doc_id}.pdf"

    if is_valid_pdf(output_path):
        print(
            f"SKIP       | {doc_id} | already exists"
        )
        return "skipped"

    print(f"FINDING PDF | {doc_id}")

    try:
        pdf_url = find_pdf_url(
            session,
            source_url,
        )

        print(f"PDF URL    | {pdf_url}")

        response = session.get(
            pdf_url,
            timeout=120,
            allow_redirects=True,
        )
        response.raise_for_status()

        content = response.content

        if not content.startswith(b"%PDF-"):
            content_type = response.headers.get(
                "Content-Type",
                "",
            )

            raise ValueError(
                f"response is not a PDF "
                f"(content-type={content_type})"
            )

        output_path.write_bytes(content)

        size_kb = len(content) / 1024

        print(
            f"DOWNLOADED | {doc_id} | "
            f"{size_kb:.1f} KB"
        )

        return "downloaded"

    except Exception as error:
        print(
            f"FAILED     | {doc_id} | {error}"
        )
        return "failed"


def load_manifest() -> list[dict]:

    with MANIFEST.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def main() -> None:

    documents = load_manifest()

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "PolicyLens/1.0 "
                "(academic research corpus)"
            )
        }
    )

    downloaded = 0
    skipped = 0
    failed = 0

    print(
        f"Documents in manifest: "
        f"{len(documents)}"
    )
    print()

    for document in documents:

        status = download_pdf(
            session,
            document,
        )

        if status == "downloaded":
            downloaded += 1

        elif status == "skipped":
            skipped += 1

        else:
            failed += 1

        time.sleep(1)

    print()
    print("========== SUMMARY ==========")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")
    print(f"Total:      {len(documents)}")


if __name__ == "__main__":
    main()