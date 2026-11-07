import argparse

import yaml

from src.embedder import Embedder
from src.filters import parse_filters
from src.vector_store import VectorStore


def load_config(config_path: str = "config.yaml") -> dict:
    """Load project configuration."""

    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def search_collection(
    store: VectorStore,
    embedder: Embedder,
    query: str,
    top_k: int,
    preview_chars: int,
    where: dict | None = None,
) -> None:
    """Search a collection and display the ranked results."""

    query_embedding = embedder.embed_texts([query])[0]

    results = store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        where=where,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        print("No results found.")
        return

    for rank, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances),
        start=1,
    ):
        # Chroma returns cosine distance.
        # Convert it to a simple similarity-style score.
        score = 1 - distance

        preview = " ".join(document.split())[:preview_chars]

        print(f"\nRank: {rank}")
        print(f"Score: {score:.4f}")
        print(f"Document: {metadata.get('title', '')}")
        print(
            f"Pages: {metadata.get('page_start', '')}"
            f"-{metadata.get('page_end', '')}"
        )
        print(f"Section: {metadata.get('section_title', '')}")
        print(f"Preview: {preview}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search the PolicyLens vector index."
    )

    parser.add_argument(
        "query",
        help="Compliance question or search query.",
    )

    parser.add_argument(
        "--collection",
        default="policylens_v1",
        help="Base collection name.",
    )

    parser.add_argument(
        "--strategy",
        choices=["fixed", "structure"],
        default="structure",
        help="Chunking strategy to search.",
    )

    parser.add_argument(
        "--top_k",
        "--top-k",
        dest="top_k",
        type=int,
        default=None,
        help="Number of results to return.",
    )

    parser.add_argument(
        "--filter",
        action="append",
        default=None,
        metavar="KEY=VALUE",
        help=(
            "Restrict results by metadata, e.g. issuer=RBI. "
            "Repeat to combine filters. Keys: issuer, doc_id, "
            "title, issue_date, document_type."
        ),
    )

    args = parser.parse_args()

    try:
        where = parse_filters(args.filter)
    except ValueError as error:
        parser.error(str(error))

    config = load_config()

    top_k = (
        args.top_k
        if args.top_k is not None
        else config["search"]["default_top_k"]
    )

    preview_chars = config["search"]["preview_chars"]

    embedder = Embedder(
        model_name=config["embedding"]["model"],
        batch_size=config["embedding"]["batch_size"],
        normalize_embeddings=config["embedding"]["normalize_embeddings"],
    )

    store = VectorStore(
        path=config["vector_store"]["path"],
        collection_name=f"{args.collection}_{args.strategy}",
    )

    print(f"\nSearching {args.strategy} collection...")
    print(f"Query: {args.query}")

    if where:
        print(f"Filter: {where}")

    search_collection(
        store=store,
        embedder=embedder,
        query=args.query,
        top_k=top_k,
        preview_chars=preview_chars,
        where=where,
    )


if __name__ == "__main__":
    main()
