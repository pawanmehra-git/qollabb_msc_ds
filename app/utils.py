"""
JSON file utilities: load, save, and ensure data files exist.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Project root: parent of /app
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(file_path: str | Path, default: Any = None) -> Any:
    """
    Load JSON from disk. If the file is missing or invalid, return `default`
    (or empty dict/list as appropriate) after optional auto-create for known paths.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        logger.info("JSON file missing, using default: %s", path)
        if default is not None:
            return default
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", path, e)
        if default is not None:
            return default
        raise
    except OSError as e:
        logger.error("Cannot read %s: %s", path, e)
        if default is not None:
            return default
        raise


def save_json(file_path: str | Path, data: Any, indent: int = 2) -> None:
    """Write JSON atomically (write temp file then replace)."""
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    ensure_data_dir()
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def data_path(name: str) -> Path:
    """Return absolute path under data/ for a filename."""
    return DATA_DIR / name
