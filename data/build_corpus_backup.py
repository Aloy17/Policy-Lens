from __future__ import annotations

import csv
import hashlib
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

import pymupdf
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
MANIFEST = DATA_DIR / "manifest.csv"
REPORT = DATA_DIR / "corpus_report.csv"

MIN_DOCS = 30
MAX_DOCS = 50
MIN_LONG_DOCS = 3

REQUEST_TIMEOUT = 60
REQUEST_DELAY = 0.7


# ---------------------------------------------------------------------
# Curated official regulatory documents.
#
# Existing files already present in data/pdfs are preserved.
# New documents are downloaded only from official regulator domains.
# ---------------------------------------------------------------------

DOCUMENTS = [

    # ================================================================
    # RBI
    # ================================================================

    (
        "RBI",
        "Master Direction - NBFC Scale Based Regulation 2023",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12550%281%29.html",
        "2023-10-19",
    ),

    (
        "RBI",
        "Master Directions on Fraud Risk Management in NBFCs",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12704.html",
        "2024-07-15",
    ),

    (
        "RBI",
        "Master Direction on Information Technology Governance Risk Controls",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12562%283%29.html",
        "2023-11-07",
    ),

    (
        "RBI",
        "Master Direction - NBFC Housing Finance Company Directions 2021",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12030%282%29.html",
        "2021-02-17",
    ),

    (
        "RBI",
        "Master Direction - Asset Reconstruction Companies Directions 2024",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12669%281%29.html",
        "2024-04-24",
    ),

    (
        "RBI",
        "Master Direction - Securitisation of Standard Assets Directions 2021",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12165.html",
        "2021-09-24",
    ),

    (
        "RBI",
        "Master Direction - Transfer of Loan Exposures Directions 2021",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12166%281%29.html",
        "2021-09-24",
    ),

    (
        "RBI",
        "Master Direction - Regulatory Framework for Microfinance Loans 2022",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12256%282%29.html",
        "2022-03-14",
    ),

    (
        "RBI",
        "Master Direction - Credit Information Companies",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D10564.html",
        "2016-06-23",
    ),

    (
        "RBI",
        "Master Direction - Peer to Peer Lending Platform",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D11137%281%29.html",
        "2017-10-04",
    ),

    (
        "RBI",
        "Master Direction - Credit Card and Debit Card Issuance and Conduct",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx_did%3D342%281%29.html",
        "2022-04-21",
    ),

    (
        "RBI",
        "Master Direction on Financial Statements - Presentation and Disclosures",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_did%3D342%281%29.html",
        "2021-08-30",
    ),

    (
        "RBI",
        "Master Direction - Filing of Supervisory Returns 2024",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx.html",
        "2024-02-27",
    ),

    (
        "RBI",
        "Master Direction - Outsourcing of Information Technology Services",
        "https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12551.html",
        "2023-04-10",
    ),

    # ================================================================
    # SEBI
    # ================================================================

    (
        "SEBI",
        "Master Circular for Alternative Investment Funds",
        "https://www.sebi.gov.in/legal/master-circulars/may-2024/master-circular-for-alternative-investment-funds-aifs-_83229.html",
        "2024-05-07",
    ),

    (
        "SEBI",
        "Master Circular for Investment Advisers",
        "https://www.sebi.gov.in/legal/master-circulars/may-2024/master-circular-for-investment-advisers_83488.html",
        "2024-05-21",
    ),

    (
        "SEBI",
        "Master Circular for Portfolio Managers",
        "https://www.sebi.gov.in/legal/master-circulars/jun-2024/master-circular-for-portfolio-managers_84026.html",
        "2024-06-07",
    ),

    (
        "SEBI",
        "Master Circular for Mutual Funds",
        "https://www.sebi.gov.in/legal/master-circulars/jun-2024/master-circular-for-mutual-funds_84441.html",
        "2024-06-27",
    ),

    (
        "SEBI",
        "Master Circular for Debenture Trustees",
        "https://www.sebi.gov.in/legal/master-circulars/may-2024/master-circular-for-debenture-trustees-dts-_83419.html",
        "2024-05-16",
    ),

    (
        "SEBI",
        "Master Circular for Credit Rating Agencies",
        "https://www.sebi.gov.in/legal/master-circulars/may-2024/master-circular-for-credit-rating-agencies-cras-_83417.html",
        "2024-05-16",
    ),

    (
        "SEBI",
        "Master Circular for Stock Brokers",
        "https://www.sebi.gov.in/legal/master-circulars/may-2024/master-circular-for-stock-brokers_83521.html",
        "2024-05-22",
    ),

    (
        "SEBI",
        "Master Circular for Listing Obligations and Disclosure Requirements",
        "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2023/1689087475880.pdf",
        "2023-07-11",
    ),

    (
        "SEBI",
        "Master Circular for Non Convertible Securities",
        "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2023/1688812243903.pdf",
        "2023-07-07",
    ),

    (
        "SEBI",
        "Master Circular for Depositories",
        "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2023/1696831738330.pdf",
        "2023-10-06",
    ),

    (
        "SEBI",
        "Master Circular for Custodians",
        "https://www.sebi.gov.in/sebi_data/attachdocs/may-2024/1715353322049.pdf",
        "2024-05-10",
    ),

    (
        "SEBI",
        "Master Circular for Registrar and Share Transfer Agents",
        "https://www.sebi.gov.in/sebi_data/attachdocs/may-2024/1715081550397.pdf",
        "2024-05-07",
    ),

    (
        "SEBI",
        "Master Circular for Research Analysts",
        "https://www.sebi.gov.in/sebi_data/attachdocs/may-2024/1716290553655.pdf",
        "2024-05-21",
    ),

    (
        "SEBI",
        "Master Circular for Online Dispute Resolution",
        "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2023/1703763993735.pdf",
        "2023-12-28",
    ),

    (
        "SEBI",
        "Master Circular for Stock Exchanges and Clearing Corporations",
        "https://www.sebi.gov.in/sebi_data/attachdocs/jan-2025/1736760771912.pdf",
        "2024-12-30",
    ),

    # ================================================================
    # PFRDA
    # ================================================================

    (
        "PFRDA",
        "Master Circular - KYC AML CFT",
        "https://www.pfrda.org.in/documents/33652/147653/Revised%2BMaster%2BCicular%2BKYC%2Bguidelines.pdf",
        "2024-09-23",
    ),
]


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

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
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def page_stats(path: Path) -> tuple[int, int, int]:
    """
    Return:
        page_count,
        low_text_page_count,
        total_extracted_words
    """

    with pymupdf.open(path) as document:
        low_text_pages = 0
        total_words = 0

        for page in document:
            text = page.get_text("text")
            words = len(text.split())

            total_words += words

            if words < 20:
                low_text_pages += 1

        return (
            len(document),
            low_text_pages,
            total_words,
        )


def slug(value: str) -> str:
    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value.lower(),
    )

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


def resolve_pdf_url(
    session: requests.Session,
    url: str,
) -> str | None:

    url = clean_url(url)

    # Direct PDF.
    if url.lower().split("?")[0].endswith(".pdf"):
        return url

    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        print(f"  RESOLVE FAILED | {exc}")
        return None

    # Some regulator pages redirect directly to a PDF.
    if response.content.startswith(b"%PDF-"):
        return response.url

    content_type = response.headers.get(
        "Content-Type",
        "",
    ).lower()

    if "html" not in content_type:
        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # Prefer links whose href explicitly ends in .pdf.
    pdf_links = []

    for anchor in soup.find_all("a", href=True):
        href = clean_url(
            urljoin(
                response.url,
                anchor["href"],
            )
        )

        text = " ".join(
            anchor.get_text(
                " ",
                strip=True,
            ).split()
        )

        score = 0

        if ".pdf" in href.lower():
            score += 5

        if "master direction" in text.lower():
            score += 3

        if "master circular" in text.lower():
            score += 3

        if "download" in text.lower():
            score += 1

        if score > 0:
            pdf_links.append(
                (
                    score,
                    href,
                )
            )

    if not pdf_links:
        return None

    pdf_links.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return pdf_links[0][1]


def download_document(
    session: requests.Session,
    item: tuple[str, str, str, str],
    used_hashes: set[str],
) -> dict | None:

    issuer, title, source_url, issue_date = item

    source_url = clean_url(source_url)

    print()
    print(f"DOWNLOAD | {issuer} | {title}")

    pdf_url = resolve_pdf_url(
        session,
        source_url,
    )

    if not pdf_url:
        print("  SKIP | could not resolve PDF")
        return None

    print(f"  PDF | {pdf_url}")

    try:
        response = session.get(
            pdf_url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        print(f"  SKIP | request failed | {exc}")
        return None

    content = response.content

    if not content.startswith(b"%PDF-"):
        print("  SKIP | response is not a PDF")
        return None

    doc_id = f"{issuer.lower()}_{slug(title)}"

    output_path = PDF_DIR / f"{doc_id}.pdf"

    # Do not overwrite a valid existing file.
    if valid_pdf(output_path):
        file_hash = sha256(output_path)

        if file_hash in used_hashes:
            print("  SKIP | already present")
            return None

    try:
        output_path.write_bytes(content)
    except OSError as exc:
        print(f"  SKIP | write failed | {exc}")
        return None

    file_hash = sha256(output_path)

    # Duplicate content check.
    if file_hash in used_hashes:
        output_path.unlink(missing_ok=True)
        print("  SKIP | duplicate PDF content")
        return None

    try:
        pages, low_text_pages, words = page_stats(
            output_path
        )
    except Exception as exc:
        output_path.unlink(missing_ok=True)
        print(f"  SKIP | PDF parsing failed | {exc}")
        return None

    if pages <= 0:
        output_path.unlink(missing_ok=True)
        print("  SKIP | zero pages")
        return None

    # Require meaningful content.
    if words < 30:
        output_path.unlink(missing_ok=True)
        print(
            f"  SKIP | too little extracted text | words={words}"
        )
        return None

    used_hashes.add(file_hash)

    document_type = (
        "scanned_or_mixed"
        if low_text_pages >= max(
            2,
            pages // 10,
        )
        else "text_native"
    )

    print(
        f"  OK | pages={pages} | words={words} | "
        f"low_text_pages={low_text_pages} | "
        f"type={document_type}"
    )

    return {
        "doc_id": doc_id,
        "title": title,
        "issuer": issuer,
        "issue_date": issue_date,
        "url": pdf_url,
        "page_count": str(pages),
        "document_type": document_type,
        "_hash": file_hash,
        "_low_text_pages": low_text_pages,
        "_words": words,
    }


def write_manifest(rows: list[dict]) -> None:

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

        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row.get(
                        field,
                        "",
                    )
                    for field in fields
                }
            )


def write_report(rows: list[dict]) -> None:

    fields = [
        "doc_id",
        "title",
        "issuer",
        "page_count",
        "document_type",
        "low_text_pages",
        "sha256",
    ]

    with REPORT.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for row in rows:

            writer.writerow(
                {
                    "doc_id": row["doc_id"],
                    "title": row["title"],
                    "issuer": row["issuer"],
                    "page_count": row["page_count"],
                    "document_type": row["document_type"],
                    "low_text_pages": row.get(
                        "_low_text_pages",
                        "",
                    ),
                    "sha256": row.get(
                        "_hash",
                        "",
                    ),
                }
            )


def main() -> None:

    PDF_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = load_existing()

    print(
        f"EXISTING | {len(existing)} manifest documents"
    )

    rows = existing[:]

    existing_ids = {
        row["doc_id"]
        for row in existing
        if row.get("doc_id")
    }

    used_hashes = set()

    # -----------------------------------------------------------------
    # Validate existing files.
    # -----------------------------------------------------------------

    valid_existing = 0

    for row in existing:

        doc_id = row.get("doc_id")

        if not doc_id:
            continue

        path = PDF_DIR / f"{doc_id}.pdf"

        if valid_pdf(path):
            used_hashes.add(
                sha256(path)
            )
            valid_existing += 1

    print(
        f"EXISTING VALID PDFs | {valid_existing}"
    )

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "PolicyLens/1.0 "
                "(academic regulatory-document retrieval project)"
            )
        }
    )

    # -----------------------------------------------------------------
    # Download curated candidates.
    # -----------------------------------------------------------------

    attempted = 0
    added = 0
    skipped = 0

    for item in DOCUMENTS:

        if len(rows) >= MAX_DOCS:
            break

        issuer, title, source_url, issue_date = item

        doc_id = f"{issuer.lower()}_{slug(title)}"

        # Existing corpus document.
        if doc_id in existing_ids:
            print(
                f"EXISTS | {issuer} | {title}"
            )
            continue

        attempted += 1

        result = download_document(
            session,
            item,
            used_hashes,
        )

        if result is None:
            skipped += 1
            continue

        rows.append(result)
        existing_ids.add(
            result["doc_id"]
        )

        added += 1

        time.sleep(
            REQUEST_DELAY
        )

    # -----------------------------------------------------------------
    # Write manifest.
    # -----------------------------------------------------------------

    write_manifest(rows)

    # -----------------------------------------------------------------
    # Recompute evidence from actual files.
    # -----------------------------------------------------------------

    report_rows = []

    for row in rows:

        doc_id = row.get("doc_id")

        if not doc_id:
            continue

        path = PDF_DIR / f"{doc_id}.pdf"

        if not valid_pdf(path):
            continue

        try:
            pages, low_text_pages, words = page_stats(
                path
            )
        except Exception:
            continue

        report_rows.append(
            {
                "doc_id": doc_id,
                "title": row.get(
                    "title",
                    "",
                ),
                "issuer": row.get(
                    "issuer",
                    "",
                ),
                "issue_date": row.get(
                    "issue_date",
                    "",
                ),
                "url": row.get(
                    "url",
                    "",
                ),
                "page_count": pages,
                "document_type": (
                    "scanned_or_mixed"
                    if low_text_pages >= max(
                        2,
                        pages // 10,
                    )
                    else "text_native"
                ),
                "_low_text_pages": low_text_pages,
                "_words": words,
                "_hash": sha256(path),
            }
        )

    write_report(
        report_rows
    )

    # -----------------------------------------------------------------
    # Corpus statistics.
    # -----------------------------------------------------------------

    issuer_counts = Counter(
        row["issuer"]
        for row in report_rows
    )

    long_docs = [
        row
        for row in report_rows
        if int(row["page_count"]) > 50
    ]

    scanned_docs = [
        row
        for row in report_rows
        if row["document_type"]
        == "scanned_or_mixed"
    ]

    total_pages = sum(
        int(row["page_count"])
        for row in report_rows
    )

    total_words = sum(
        int(row["_words"])
        for row in report_rows
    )

    # -----------------------------------------------------------------
    # Summary.
    # -----------------------------------------------------------------

    print()
    print("=" * 60)
    print("CORPUS SUMMARY")
    print("=" * 60)

    print(
        f"Documents:              {len(report_rows)}"
    )

    print(
        f"Target range:           {MIN_DOCS}-{MAX_DOCS}"
    )

    print(
        f"Total pages:            {total_pages}"
    )

    print(
        f"Total extracted words:  {total_words}"
    )

    print(
        f"Documents >50 pages:    "
        f"{len(long_docs)} / {MIN_LONG_DOCS} required"
    )

    print(
        f"Scanned/mixed docs:     {len(scanned_docs)}"
    )

    print(
        f"New documents added:    {added}"
    )

    print(
        f"Candidates attempted:   {attempted}"
    )

    print(
        f"Candidates skipped:     {skipped}"
    )

    print()
    print("ISSUERS")

    for issuer, count in sorted(
        issuer_counts.items()
    ):
        print(
            f"  {issuer}: {count}"
        )

    print()
    print(
        f"PDF directory:          {PDF_DIR}"
    )

    print(
        f"Manifest:               {MANIFEST}"
    )

    print(
        f"Report:                 {REPORT}"
    )

    # -----------------------------------------------------------------
    # Compliance checks.
    # -----------------------------------------------------------------

    failures = []

    if not (
        MIN_DOCS
        <= len(report_rows)
        <= MAX_DOCS
    ):
        failures.append(
            "document count is outside 30-50"
        )

    if len(long_docs) < MIN_LONG_DOCS:
        failures.append(
            "fewer than 3 documents exceed 50 pages"
        )

    if len(issuer_counts) < 3:
        failures.append(
            "fewer than 3 issuers represented"
        )

    if failures:

        print()
        print(
            "CORPUS STATUS: NOT YET COMPLIANT"
        )

        for failure in failures:
            print(
                f" - {failure}"
            )

        print()
        print(
            "No claim of assignment compliance is made."
        )

        raise SystemExit(2)

    print()
    print(
        "CORPUS STATUS: BASIC REQUIREMENTS MET"
    )

    print()
    print(
        "The corpus is ready for the ingestion pipeline."
    )


if __name__ == "__main__":
    main()