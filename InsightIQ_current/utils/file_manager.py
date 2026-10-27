import json
from pathlib import Path

from .settings import APP_DIR


RECENTS_PATH = APP_DIR / "recent_files.json"


def load_recent_files():
    try:
        data = json.loads(RECENTS_PATH.read_text(encoding="utf-8"))
        return [p for p in data if Path(p).exists()]
    except (OSError, ValueError, TypeError):
        return []


def add_recent_file(path):
    path = str(Path(path).resolve())
    items = [p for p in load_recent_files() if p != path]
    items.insert(0, path)
    _save(items[:10])


def remove_recent_file(path):
    _save([p for p in load_recent_files() if p != path])


def clear_recent_files():
    _save([])


def _save(items):
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        RECENTS_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
    except OSError:
        pass