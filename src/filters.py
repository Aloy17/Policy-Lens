"""Parse --filter key=value arguments into a Chroma `where` clause."""

import csv
from pathlib import Path
from typing import Any

ALLOWED_KEYS = {
    "issuer",
    "doc_id",
    "title",
    "issue_date",
    "document_type",
}

# Short names people type on the command line -> value stored in metadata.
ISSUER_ALIASES = {
    "RBI": "Reserve Bank of India",
}


def _known_issuers(manifest_path: str | Path) -> list[str]:
    """Return the distinct issuer names found in the manifest."""
    path = Path(manifest_path)

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as file:
        return sorted(
            {
                row["issuer"]
                for row in csv.DictReader(file)
                if row.get("issuer")
            }
        )


def _resolve_issuer(value: str, manifest_path: str | Path) -> str:
    """Resolve aliases and letter case to the stored issuer name."""
    alias = ISSUER_ALIASES.get(value.strip().upper())

    if alias:
        return alias

    for issuer in _known_issuers(manifest_path):
        if issuer.lower() == value.strip().lower():
            return issuer

    return value.strip()


def parse_filters(
    filters: list[str] | None,
    manifest_path: str | Path = "data/manifest.csv",
) -> dict[str, Any] | None:
    """
    Turn ["issuer=RBI", "document_type=text_native"] into a Chroma where clause.

    Returns None when no filters are given.
    Raises ValueError for malformed filters or unknown keys.
    """
    if not filters:
        return None

    conditions = []

    for item in filters:
        if "=" not in item:
            raise ValueError(
                f"Invalid filter '{item}'. Use key=value, "
                f"for example issuer=RBI."
            )

        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key not in ALLOWED_KEYS:
            raise ValueError(
                f"Unknown filter key '{key}'. "
                f"Allowed keys: {', '.join(sorted(ALLOWED_KEYS))}."
            )

        if not value:
            raise ValueError(f"Filter '{item}' has an empty value.")

        if key == "issuer":
            value = _resolve_issuer(value, manifest_path)

        conditions.append({key: value})

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}
