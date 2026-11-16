from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))

from export_index_evidence import passage_quality, select_representative_records


def make_record(record_id, doc_id, page, passage, section="", ocr=False):
    return {
        "id": record_id,
        "metadata": {
            "doc_id": doc_id,
            "page_start": page,
            "page_end": page,
            "section_title": section,
            "ocr_used": ocr,
            "document_type": "text_native",
        },
        "document": passage,
    }


class FakeCollection:
    def __init__(self, records):
        self.records = records

    def count(self):
        return len(self.records)

    def get(self, limit, offset, include):
        batch = self.records[offset:offset + limit]
        return {
            "ids": [record["id"] for record in batch],
            "metadatas": [record["metadata"] for record in batch],
            "documents": [record["document"] for record in batch],
        }


GOOD = (
    "The intermediary shall maintain adequate records of every transaction and "
    "ensure that the compliance officer reviews the records periodically. "
) * 3


def test_passage_quality_rejects_garbled_hindi_and_accepts_english():
    garbled = "दवारा अपिाए रए एलरोररिडमक सडहत तकिीकी उपायो " * 20
    assert passage_quality(GOOD, {}) > passage_quality(garbled, {})
    assert passage_quality(GOOD, {}) >= 0.58


def test_selector_excludes_boilerplate_and_diversifies_documents():
    records = [
        make_record("footer", "gazette", 3,
                    "Printed by the General Manager, Government of India Press. " * 8),
        make_record("a1", "doc-a", 10, GOOD, "Chapter I: General requirements"),
        make_record("a2", "doc-a", 20, GOOD + "Additional substantive text. " * 2,
                    "Chapter II: Compliance obligations"),
        make_record("b1", "doc-b", 30, GOOD, "Chapter III: Record keeping"),
        make_record("c1", "doc-c", 40, GOOD, "Chapter IV: Reporting"),
    ]
    selected = select_representative_records(FakeCollection(records), 3)
    assert len(selected) == 3
    assert len({item["metadata"]["doc_id"] for item in selected}) == 3
    assert "footer" not in {item["id"] for item in selected}


def test_selector_returns_empty_when_all_candidates_are_unreadable():
    garbled = "दवारा अपिाए रए एलरोररिडमक सडहत तकिीकी उपायो " * 20
    collection = FakeCollection([
        make_record("bad", "doc-bad", 10, garbled, "Chapter I: Test")
    ])
    assert select_representative_records(collection, 5) == []
