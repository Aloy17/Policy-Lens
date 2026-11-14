import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))

from chunk_stats import is_table_fragment, summarize  # noqa: E402
from ocr_accuracy import edit_distance, score  # noqa: E402


def words(count):
    return " ".join(["w"] * count)


def test_summarize_counts_short_and_long_chunks():
    texts = [words(100), words(400), words(900)]
    result = summarize(texts, lambda text: len(text.split()))
    assert result["chunks"] == 3
    assert result["below_300"] == 1
    assert result["above_800"] == 1
    assert result["min"] == 100 and result["max"] == 900


def test_table_fragment_detection():
    assert is_table_fragment("| a | b |\n| 1 | 2 |")
    assert not is_table_fragment("[TABLE 1]\n| a | b |\n| --- | --- |")
    assert not is_table_fragment("Plain paragraph text.")


def test_edit_distance_basic():
    assert edit_distance("a b c".split(), "a b c".split()) == 0
    assert edit_distance("a b c".split(), "a x c".split()) == 1
    assert edit_distance("a b c".split(), "a c".split()) == 1


def test_score_perfect_and_noisy_ocr():
    perfect = score("one two three four", "one two three four")
    assert perfect["word_accuracy"] == 1.0 and perfect["word_recall"] == 1.0
    noisy = score("one two three four", "header one two thre four")
    assert noisy["word_recall"] == 0.75
    assert noisy["word_errors"] == 2
