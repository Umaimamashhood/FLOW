"""Client for the local Ollama service (SRS 3.1.3, FR-41, FR-42, 4.3.1)."""
from __future__ import annotations

import time

import requests

from flow import config


def list_models() -> list[str]:
    resp = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
    resp.raise_for_status()
    return [m["name"] for m in resp.json().get("models", [])]


def status() -> dict:
    info = {"model": config.OLLAMA_MODEL, "reachable": False, "model_installed": False, "error": None}
    if config.MOCK_MODE:
        return {**info, "reachable": True, "model_installed": True, "mock": True}
    try:
        models = list_models()
    except (requests.RequestException, ValueError):
        info["error"] = "Ollama is not running. Start the Ollama app (or run 'ollama serve') and try again."
        return info
    info["reachable"] = True
    info["model_installed"] = bool({config.OLLAMA_MODEL, f"{config.OLLAMA_MODEL}:latest"} & set(models))
    if not info["model_installed"]:
        info["error"] = f"Model '{config.OLLAMA_MODEL}' is not installed. Run: ollama pull {config.OLLAMA_MODEL}"
    return info


def generate(prompt: str, system: str = "", json_mode: bool = False) -> str:
    if config.MOCK_MODE:
        raise RuntimeError("LLM is disabled in mock mode")
    body = {"model": config.OLLAMA_MODEL, "prompt": prompt, "system": system,
            "stream": False, "options": {"temperature": 0.2}}
    if json_mode:
        body["format"] = "json"
    last_error: Exception | None = None
    for _ in range(config.LLM_RETRY_COUNT):
        try:
            resp = requests.post(f"{config.OLLAMA_URL}/api/generate", json=body, timeout=120)
            resp.raise_for_status()
            return resp.json()["response"]
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(config.LLM_RETRY_DELAY)
    raise ConnectionError(f"Ollama request failed after {config.LLM_RETRY_COUNT} attempts: {last_error}")
