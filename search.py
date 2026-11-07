import argparse
import os
import yaml

from src.embedder import Embedder
from src.filters import parse_filters
from src.vector_store import VectorStore
from src.runtime_paths import app_path, data_path


def load_config(config_path: str = "config.yaml") -> dict:
    with app_path(config_path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def search_collection(store, embedder, query, top_k, preview_chars, where=None):
    query_embedding = embedder.embed_texts([query])[0]
    results = store.search(query_embedding=query_embedding, top_k=top_k, where=where)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    if not documents:
        print("No results found.")
        return
    for rank, (document, metadata, distance) in enumerate(zip(documents, metadatas, distances), start=1):
        print(f"\nRank: {rank}")
        print(f"Score: {1-distance:.4f}")
        print(f"Document: {metadata.get('title', '')}")
        print(f"Pages: {metadata.get('page_start', '')}-{metadata.get('page_end', '')}")
        print(f"Section: {metadata.get('section_title', '')}")
        print(f"Preview: {' '.join(document.split())[:preview_chars]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the PolicyLens vector index.")
    parser.add_argument("query", help="Compliance question or search query.")
    parser.add_argument("--collection", default="policylens_v1", help="Base collection name.")
    parser.add_argument("--strategy", choices=["fixed", "structure"], default="structure")
    parser.add_argument("--top_k", "--top-k", dest="top_k", type=int, default=None)
    parser.add_argument("--filter", action="append", default=None, metavar="KEY=VALUE")
    args = parser.parse_args()
    manifest_path = os.environ.get("POLICYLENS_MANIFEST_PATH", str(data_path("data/manifest.csv")))
    try:
        where = parse_filters(args.filter, manifest_path=manifest_path)
    except ValueError as error:
        parser.error(str(error))
    config = load_config()
    top_k = args.top_k if args.top_k is not None else config["search"]["default_top_k"]
    embedder = Embedder(model_name=config["embedding"]["model"],
        batch_size=config["embedding"]["batch_size"],
        normalize_embeddings=config["embedding"]["normalize_embeddings"])
    store = VectorStore(path=str(data_path(config["vector_store"]["path"])),
                        collection_name=f"{args.collection}_{args.strategy}")
    print(f"\nSearching {args.strategy} collection...")
    print(f"Query: {args.query}")
    if where:
        print(f"Filter: {where}")
    search_collection(store, embedder, args.query, top_k,
                      config["search"]["preview_chars"], where)


if __name__ == "__main__":
    main()
