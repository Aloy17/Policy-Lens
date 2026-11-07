from pathlib import Path

from src.runtime_paths import APP_ROOT, DATA_ROOT, app_path, data_path


def test_default_paths_use_project_root():
    assert APP_ROOT == Path(__file__).resolve().parents[1]
    assert DATA_ROOT == APP_ROOT
    assert app_path("config.yaml") == APP_ROOT / "config.yaml"
    assert data_path("chroma_db") == APP_ROOT / "chroma_db"


def test_absolute_paths_are_preserved(tmp_path):
    absolute = tmp_path / "outside"
    assert app_path(absolute) == absolute
    assert data_path(absolute) == absolute
