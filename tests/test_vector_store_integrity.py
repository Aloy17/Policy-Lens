from src.vector_store import VectorStore


class FakeCollection:
    def __init__(self, metadatas):
        self.metadatas = metadatas

    def get(self, where, include):
        assert include == ["metadatas"]
        assert where == {
            "$and": [
                {"doc_id": "doc-1"},
                {"source_hash": "abc123"},
            ]
        }
        return {"metadatas": self.metadatas}


def make_store(metadatas):
    store = VectorStore.__new__(VectorStore)
    store.collection = FakeCollection(metadatas)
    return store


def metadata(index, count=3, strategy="fixed"):
    return {
        "doc_id": "doc-1",
        "source_hash": "abc123",
        "chunk_strategy": strategy,
        "chunk_index": index,
        "chunk_count": count,
    }


def test_complete_version_is_recognized():
    store = make_store([metadata(0), metadata(1), metadata(2)])

    assert store.has_complete_document_version(
        "doc-1", "abc123", expected_chunk_count=None, chunk_strategy="fixed"
    )


def test_incomplete_version_is_not_recognized():
    store = make_store([metadata(0), metadata(2)])

    assert not store.has_complete_document_version(
        "doc-1", "abc123", expected_chunk_count=None, chunk_strategy="fixed"
    )


def test_duplicate_chunk_index_is_not_recognized():
    store = make_store([metadata(0), metadata(1), metadata(1)])

    assert not store.has_complete_document_version(
        "doc-1", "abc123", expected_chunk_count=None, chunk_strategy="fixed"
    )


def test_wrong_chunk_strategy_is_not_recognized():
    store = make_store([metadata(0, strategy="structure"), metadata(1, strategy="structure"),
                        metadata(2, strategy="structure")])

    assert not store.has_complete_document_version(
        "doc-1", "abc123", expected_chunk_count=None, chunk_strategy="fixed"
    )


def test_inconsistent_expected_chunk_counts_are_not_recognized():
    store = make_store([metadata(0), metadata(1, count=4), metadata(2)])

    assert not store.has_complete_document_version(
        "doc-1", "abc123", expected_chunk_count=None, chunk_strategy="fixed"
    )


def test_known_expected_chunk_count_must_match():
    store = make_store([metadata(0), metadata(1), metadata(2)])

    assert not store.has_complete_document_version(
        "doc-1", "abc123", expected_chunk_count=4, chunk_strategy="fixed"
    )


def test_empty_version_is_not_recognized():
    store = make_store([])

    assert not store.has_complete_document_version(
        "doc-1", "abc123", expected_chunk_count=None, chunk_strategy="fixed"
    )
