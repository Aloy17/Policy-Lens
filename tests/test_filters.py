import pytest

from src.filters import parse_filters


def test_no_filters_returns_none():
    assert parse_filters(None) is None
    assert parse_filters([]) is None


def test_rbi_alias_resolves_to_full_issuer_name():
    assert parse_filters(["issuer=RBI"]) == {
        "issuer": "Reserve Bank of India"
    }


def test_issuer_is_case_insensitive_against_manifest():
    assert parse_filters(["issuer=sebi"], "data/manifest.csv") == {
        "issuer": "SEBI"
    }


def test_multiple_filters_are_combined_with_and():
    where = parse_filters(
        ["issuer=RBI", "document_type=text_native"]
    )

    assert where == {
        "$and": [
            {"issuer": "Reserve Bank of India"},
            {"document_type": "text_native"},
        ]
    }


def test_unknown_key_is_rejected():
    with pytest.raises(ValueError):
        parse_filters(["colour=blue"])


def test_missing_equals_is_rejected():
    with pytest.raises(ValueError):
        parse_filters(["issuer"])
