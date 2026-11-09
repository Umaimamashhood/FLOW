"""User settings: defaults overridden by values in the preferences table (FR-39, SRS 3.1.1 item 7)."""
from __future__ import annotations

import json
from pathlib import Path

from flow import config, db

POLICIES = ("Always Confirm", "Confirm Destructive Only", "Unattended")


def _defaults() -> dict:
    return {
        "default_projects_dir": str(config.PROJECTS_DIR),
        "default_browser": "default",
        "search_engine": "google",
        "coding_language": "python",
        "vscode_path": "",
        "ollama_model": config.OLLAMA_MODEL,
        "voice_output": True,
        "wake_word": "",  # stored for future use; wake word detection is not implemented yet
        "push_to_talk_key": "Ctrl+Space",
        "confirmation_policy": "Always Confirm",
        "history_enabled": True,
        "asr_confidence_min": config.ASR_CONFIDENCE_MIN,
    }


def get() -> dict:
    merged = _defaults()
    for key, raw in db.all_prefs().items():
        if key in merged:
            try:
                merged[key] = json.loads(raw)
            except json.JSONDecodeError:
                pass
    return merged


def update(values: dict) -> dict:
    defaults = _defaults()
    for key, value in values.items():
        if key not in defaults:
            raise ValueError(f"unknown setting: {key}")
        if type(value) is not type(defaults[key]):
            raise ValueError(f"{key} must be of type {type(defaults[key]).__name__}")
    if "confirmation_policy" in values and values["confirmation_policy"] not in POLICIES:
        raise ValueError(f"confirmation_policy must be one of: {', '.join(POLICIES)}")
    if "asr_confidence_min" in values and not 0 <= values["asr_confidence_min"] <= 1:
        raise ValueError("asr_confidence_min must be between 0 and 1")
    if "default_projects_dir" in values and not Path(values["default_projects_dir"]).is_absolute():
        raise ValueError("default_projects_dir must be an absolute path")
    for key, value in values.items():
        db.set_pref(key, json.dumps(value))
    apply_runtime()
    return get()


def apply_runtime() -> None:
    """Push settings that other modules read from config at call time."""
    current = get()
    config.OLLAMA_MODEL = current["ollama_model"]
    config.PROJECTS_DIR = Path(current["default_projects_dir"])
    if config.PROJECTS_DIR not in config.ALLOWED_DIRS:
        config.ALLOWED_DIRS.append(config.PROJECTS_DIR)
