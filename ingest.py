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
from src.runtime_paths import app_path, data_path


def setup_logging(config: dict) -> logging.Logger:
    log_file = data_path(config["logging"]["ingestion_log"])
    error_file = data_path(config["logging"]["error_log"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    error_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("policylens")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    error_logger = logging.getLogger("policylens.errors")
    error_logger.setLevel(logging.ERROR)
    error_logger.handlers.clear()
    error_handler = logging.FileHandler(error_file, encoding="utf-8")
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    return logger


def load_config(config_path: str = "config.yaml") -> dict:
    with app_path(config_path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_manifest(manifest_path: str) -> pd.DataFrame:
    return pd.read_csv(manifest_path)


def get_existing_source_hashes(store: VectorStore, doc_id: str) -> set[str]:
    result = store.collection.get(where={"doc_id": doc_id}, include=["metadatas"])
    metadatas = result.get("metadatas", [])
    return {item["source_hash"] for item in metadatas if item.get("source_hash")}


def process_document(pdf_path: Path, document: dict, config: dict, embedder: Embedder,
                     fixed_store: VectorStore, structure_store: VectorStore,
                     logger: logging.Logger) -> dict:
    doc_id = str(document["doc_id"])
    start_time = time.perf_counter()
    logger.info("PROCESSING | %s", pdf_path.name)
    source_hash = calculate_file_hash(pdf_path)
    existing_hashes = get_existing_source_hashes(structure_store, doc_id)
    fixed_hashes = get_existing_source_hashes(fixed_store, doc_id)
    fixed_complete = (
        fixed_hashes == {source_hash}
        and fixed_store.has_complete_document_version(
            doc_id, source_hash, expected_chunk_count=None,
            chunk_strategy="fixed",
        )
    )
    structure_complete = (
        existing_hashes == {source_hash}
        and structure_store.has_complete_document_version(
            doc_id, source_hash, expected_chunk_count=None,
            chunk_strategy="structure",
        )
    )
    if fixed_complete and structure_complete:
        logger.info("SKIP | %s | unchanged and complete in both indexes", doc_id)
        return {"status": "skipped", "doc_id": doc_id, "pages": 0, "ocr_pages": 0,
                "fixed_chunks": 0, "structure_chunks": 0,
                "seconds": time.perf_counter() - start_time}
    if existing_hashes or fixed_hashes:
        logger.info("UPDATE | %s | source hash changed or index incomplete", doc_id)
    pages = parse_pdf(pdf_path)
    pages = apply_ocr_to_pages(
        pdf_path, pages,
        min_words=config["ocr"]["min_words_per_page"],
        language=config["ocr"]["language"],
        enabled=config["ocr"].get("enabled", True),
        image_coverage_threshold=config["ocr"].get("image_coverage_threshold", 0.5),
        image_text_word_limit=config["ocr"].get("image_text_word_limit", 120),
    )
    ocr_pages = sum(1 for page in pages if page.get("ocr_used", False))
    pages = clean_pages(pages)
    fixed_chunks = fixed_size_chunks(pages,
        chunk_size=config["chunking"]["fixed"]["chunk_size"],
        overlap=config["chunking"]["fixed"]["overlap"],
        tokenizer=embedder.tokenizer)
    fixed_chunks = attach_metadata(fixed_chunks, document, source_hash, "fixed")
    structure_chunks = structure_aware_chunks(pages,
        target_size=config["chunking"]["structure"]["target_size"],
        max_size=config["chunking"]["structure"]["max_size"],
        min_size=config["chunking"]["structure"]["min_size"],
        tokenizer=embedder.tokenizer)
    structure_chunks = attach_metadata(structure_chunks, document, source_hash, "structure")
    logger.info("CHUNKS | %s | fixed=%d structure=%d", doc_id,
                len(fixed_chunks), len(structure_chunks))
    if not fixed_chunks or not structure_chunks:
        raise ValueError(
            f"{doc_id}: parsing produced no chunks for one or both strategies; "
            "the existing indexed version has been preserved."
        )
    fixed_chunks = embedder.embed_chunks(fixed_chunks)
    structure_chunks = embedder.embed_chunks(structure_chunks)
    # Store the new version before removing the previous indexed version.
    fixed_store.add_chunks(fixed_chunks)
    structure_store.add_chunks(structure_chunks)
    fixed_store.delete_old_versions(doc_id, source_hash)
    structure_store.delete_old_versions(doc_id, source_hash)
    elapsed = time.perf_counter() - start_time
    logger.info("INGESTED | %s | pages=%d ocr_pages=%d fixed_chunks=%d structure_chunks=%d time=%.2fs",
                doc_id, len(pages), ocr_pages, len(fixed_chunks), len(structure_chunks), elapsed)
    return {"status": "ingested", "doc_id": doc_id, "pages": len(pages),
            "ocr_pages": ocr_pages, "fixed_chunks": len(fixed_chunks),
            "structure_chunks": len(structure_chunks), "seconds": elapsed}


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PolicyLens PDF documents.")
    parser.add_argument("--input", required=True, help="Directory containing PDF files.")
    parser.add_argument("--manifest", required=True, help="Path to manifest.csv.")
    parser.add_argument("--collection", required=True, help="Base collection name.")
    args = parser.parse_args()
    config = load_config()
    logger = setup_logging(config)
    run_start = time.perf_counter()
    logger.info("=" * 70)
    logger.info("PolicyLens ingestion started")
    input_dir = Path(args.input).expanduser().resolve()
    manifest = load_manifest(args.manifest)
    logger.info("Manifest documents: %d", len(manifest))
    embedder = Embedder(model_name=config["embedding"]["model"],
        batch_size=config["embedding"]["batch_size"],
        normalize_embeddings=config["embedding"]["normalize_embeddings"])
    db_path = str(data_path(config["vector_store"]["path"]))
    fixed_store = VectorStore(path=db_path, collection_name=f"{args.collection}_fixed")
    structure_store = VectorStore(path=db_path, collection_name=f"{args.collection}_structure")
    counts = {"ingested": 0, "skipped": 0, "failed": 0, "missing": 0}
    totals = {"pages": 0, "ocr_pages": 0, "fixed_chunks": 0, "structure_chunks": 0}
    for _, row in manifest.iterrows():
        document = row.to_dict()
        doc_id = str(document["doc_id"])
        pdf_path = input_dir / f"{doc_id}.pdf"
        if not pdf_path.exists():
            counts["missing"] += 1
            logger.warning("MISSING | %s | %s", doc_id, pdf_path)
            continue
        try:
            result = process_document(pdf_path, document, config, embedder,
                                      fixed_store, structure_store, logger)
            counts[result["status"]] += 1
            for key in totals:
                totals[key] += result[key]
        except Exception as error:
            counts["failed"] += 1
            logger.error("FAILED | %s | %s", doc_id, error, exc_info=True)
            logging.getLogger("policylens.errors").error(
                "FAILED | %s | %s", doc_id, error, exc_info=True)
    elapsed = time.perf_counter() - run_start
    logger.info("Ingestion complete | %s | %s | seconds=%.2f",
                counts, totals, elapsed)
    print("\nIngestion complete.")
    for key, value in counts.items():
        print(f"{key.title()}: {value}")
    for key, value in totals.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
