import argparse
import logging
import time
from pathlib import Path

import pandas as pd
import yaml

from src.parser import parse_pdf
from src.ocr import apply_ocr_to_pages
from src.cleaner import clean_pages
from src.chunker import fixed_size_chunks, structure_aware_chunks
from src.metadata import calculate_file_hash, attach_metadata
from src.embedder import Embedder
from src.vector_store import VectorStore


def setup_logging(config: dict) -> logging.Logger:
    """Configure console, ingestion, and error logging."""
    log_file = Path(config["logging"]["ingestion_log"])
    error_file = Path(config["logging"]["error_log"])

    log_file.parent.mkdir(parents=True, exist_ok=True)
    error_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("policylens")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    error_logger = logging.getLogger("policylens.errors")
    error_logger.setLevel(logging.ERROR)
    error_logger.handlers.clear()

    error_handler = logging.FileHandler(error_file, encoding="utf-8")
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)

    return logger


def load_config(config_path: str = "config.yaml") -> dict:
    """Load project configuration."""
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_manifest(manifest_path: str) -> pd.DataFrame:
    """Load the PDF manifest."""
    return pd.read_csv(manifest_path)


def get_existing_source_hash(
    store: VectorStore,
    doc_id: str,
) -> str | None:
    """Return the source hash already stored for a document."""
    result = store.collection.get(
        where={"doc_id": doc_id},
        include=["metadatas"],
    )

    metadatas = result.get("metadatas", [])

    if not metadatas:
        return None

    return metadatas[0].get("source_hash")


def process_document(
    pdf_path: Path,
    document: dict,
    config: dict,
    embedder: Embedder,
    fixed_store: VectorStore,
    structure_store: VectorStore,
    logger: logging.Logger,
) -> dict:
    """
    Parse, OCR, clean, chunk, embed, and index one document.

    Returns a statistics dictionary for reporting.
    """
    doc_id = str(document["doc_id"])
    start_time = time.perf_counter()

    logger.info("PROCESSING | %s", pdf_path.name)

    source_hash = calculate_file_hash(pdf_path)

    existing_hash = get_existing_source_hash(
        structure_store,
        doc_id,
    )

    if existing_hash == source_hash:
        logger.info(
            "SKIP | %s | unchanged source_hash=%s",
            doc_id,
            source_hash[:12],
        )

        return {
            "status": "skipped",
            "doc_id": doc_id,
            "pages": 0,
            "ocr_pages": 0,
            "fixed_chunks": 0,
            "structure_chunks": 0,
            "seconds": time.perf_counter() - start_time,
        }

    if existing_hash is not None:
        logger.info(
            "UPDATE | %s | source hash changed: %s -> %s",
            doc_id,
            existing_hash[:12],
            source_hash[:12],
        )

        fixed_store.delete_document(doc_id)
        structure_store.delete_document(doc_id)

    # 1. Parse
    pages = parse_pdf(pdf_path)

    # 2. OCR fallback
    pages = apply_ocr_to_pages(
        pdf_path,
        pages,
        min_words=config["ocr"]["min_words_per_page"],
        language=config["ocr"]["language"],
    )

    ocr_pages = sum(
        1 for page in pages if page.get("ocr_used", False)
    )

    # 3. Clean
    pages = clean_pages(pages)

    # 4. Fixed-size chunks
    fixed_chunks = fixed_size_chunks(
        pages,
        chunk_size=config["chunking"]["fixed"]["chunk_size"],
        overlap=config["chunking"]["fixed"]["overlap"],
    )

    fixed_chunks = attach_metadata(
        fixed_chunks,
        document,
        source_hash,
        "fixed",
    )

    # 5. Structure-aware chunks
    structure_chunks = structure_aware_chunks(
        pages,
        target_size=config["chunking"]["structure"]["target_size"],
        max_size=config["chunking"]["structure"]["max_size"],
        min_size=config["chunking"]["structure"]["min_size"],
    )

    structure_chunks = attach_metadata(
        structure_chunks,
        document,
        source_hash,
        "structure",
    )

    logger.info(
        "CHUNKS | %s | fixed=%d structure=%d",
        doc_id,
        len(fixed_chunks),
        len(structure_chunks),
    )

    # 6. Embed
    fixed_chunks = embedder.embed_chunks(fixed_chunks)
    structure_chunks = embedder.embed_chunks(structure_chunks)

    # 7. Index
    fixed_store.add_chunks(fixed_chunks)
    structure_store.add_chunks(structure_chunks)

    elapsed = time.perf_counter() - start_time

    logger.info(
        "INGESTED | %s | pages=%d ocr_pages=%d "
        "fixed_chunks=%d structure_chunks=%d time=%.2fs",
        doc_id,
        len(pages),
        ocr_pages,
        len(fixed_chunks),
        len(structure_chunks),
        elapsed,
    )

    return {
        "status": "ingested",
        "doc_id": doc_id,
        "pages": len(pages),
        "ocr_pages": ocr_pages,
        "fixed_chunks": len(fixed_chunks),
        "structure_chunks": len(structure_chunks),
        "seconds": elapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest PolicyLens PDF documents."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing PDF files.",
    )

    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to manifest.csv.",
    )

    parser.add_argument(
        "--collection",
        required=True,
        help="Base collection name for the PolicyLens index.",
    )

    args = parser.parse_args()

    config = load_config()
    logger = setup_logging(config)

    run_start = time.perf_counter()

    logger.info("=" * 70)
    logger.info("PolicyLens ingestion started")
    logger.info("=" * 70)

    input_dir = Path(args.input)
    manifest = load_manifest(args.manifest)

    logger.info(
        "Manifest documents: %d",
        len(manifest),
    )

    # Load the embedding model once per run.
    embedder = Embedder(
        model_name=config["embedding"]["model"],
        batch_size=config["embedding"]["batch_size"],
        normalize_embeddings=config["embedding"]["normalize_embeddings"],
    )

    fixed_store = VectorStore(
        path=config["vector_store"]["path"],
        collection_name=f"{args.collection}_fixed",
    )

    structure_store = VectorStore(
        path=config["vector_store"]["path"],
        collection_name=f"{args.collection}_structure",
    )

    ingested_count = 0
    skipped_count = 0
    failed_count = 0
    missing_count = 0

    total_pages = 0
    total_ocr_pages = 0
    total_fixed_chunks = 0
    total_structure_chunks = 0

    for _, row in manifest.iterrows():
        document = row.to_dict()
        doc_id = str(document["doc_id"])
        pdf_path = input_dir / f"{doc_id}.pdf"

        if not pdf_path.exists():
            missing_count += 1

            logger.warning(
                "MISSING | %s | %s",
                doc_id,
                pdf_path,
            )

            continue

        try:
            result = process_document(
                pdf_path=pdf_path,
                document=document,
                config=config,
                embedder=embedder,
                fixed_store=fixed_store,
                structure_store=structure_store,
                logger=logger,
            )

            if result["status"] == "ingested":
                ingested_count += 1
                total_pages += result["pages"]
                total_ocr_pages += result["ocr_pages"]
                total_fixed_chunks += result["fixed_chunks"]
                total_structure_chunks += result["structure_chunks"]

            elif result["status"] == "skipped":
                skipped_count += 1

        except Exception as error:
            failed_count += 1

            logger.error(
                "FAILED | %s | %s",
                doc_id,
                error,
                exc_info=True,
            )

            error_logger = logging.getLogger("policylens.errors")

            error_logger.error(
                "FAILED | %s | %s",
                doc_id,
                error,
                exc_info=True,
            )

    total_seconds = time.perf_counter() - run_start

    fixed_count = fixed_store.count()
    structure_count = structure_store.count()

    logger.info("=" * 70)
    logger.info("PolicyLens ingestion complete")
    logger.info("=" * 70)

    logger.info(
        "Documents | ingested=%d skipped=%d failed=%d missing=%d",
        ingested_count,
        skipped_count,
        failed_count,
        missing_count,
    )

    logger.info(
        "Processed pages=%d | OCR pages=%d",
        total_pages,
        total_ocr_pages,
    )

    logger.info(
        "Chunks | fixed=%d structure=%d",
        total_fixed_chunks,
        total_structure_chunks,
    )

    logger.info(
        "Collections | fixed=%d structure=%d",
        fixed_count,
        structure_count,
    )

    logger.info(
        "Total ingestion time: %.2f seconds",
        total_seconds,
    )

    if total_pages:
        logger.info(
            "Ingestion speed: %.2f seconds / 100 pages",
            total_seconds / total_pages * 100,
        )

    logger.info("=" * 70)

    print("\nIngestion complete.")
    print(f"Ingested: {ingested_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Failed: {failed_count}")
    print(f"Missing: {missing_count}")
    print(f"Pages processed: {total_pages}")
    print(f"OCR pages: {total_ocr_pages}")
    print(f"Fixed chunks: {total_fixed_chunks}")
    print(f"Structure chunks: {total_structure_chunks}")
    print(f"Fixed collection: {fixed_count}")
    print(f"Structure collection: {structure_count}")
    print(f"Total time: {total_seconds:.2f}s")


if __name__ == "__main__":
    main()
