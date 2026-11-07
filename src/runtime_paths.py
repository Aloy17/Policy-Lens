"""Path resolution for source and portable application modes."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = Path(os.environ.get("POLICYLENS_APP_DIR", PROJECT_ROOT)).expanduser().resolve()
DATA_ROOT = Path(os.environ.get("POLICYLENS_DATA_DIR", APP_ROOT)).expanduser().resolve()


def app_path(path):
    path = Path(path).expanduser()
    return path if path.is_absolute() else APP_ROOT / path


def data_path(path):
    path = Path(path).expanduser()
    return path if path.is_absolute() else DATA_ROOT / path
