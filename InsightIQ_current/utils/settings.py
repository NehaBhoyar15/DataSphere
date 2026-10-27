
import json
from pathlib import Path


APP_DIR = Path.home() / ".ai_data_analytics_assistant"
SETTINGS_PATH = APP_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "chart_type": "Bar",
    "font_size": 10,
    "recent_files": [],
}


def load_settings():
    try:
        if SETTINGS_PATH.exists():
            raw = json.loads(
                SETTINGS_PATH.read_text(encoding="utf-8")
            )
            return {**DEFAULT_SETTINGS, **raw}
    except (OSError, ValueError):
        pass

    return dict(DEFAULT_SETTINGS)


def save_settings(values):
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(
            json.dumps(values, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False
