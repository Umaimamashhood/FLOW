"""Common agent interface and shared helpers (SRS 4.3.4)."""
from __future__ import annotations

import os
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import config


@dataclass
class Result:
    ok: bool
    message: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    needs_confirmation: bool = False


def find_chrome() -> str | None:
    exe = shutil.which("chrome")
    if exe:
        return exe
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")):
        if base:
            candidate = Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def open_url(url: str, browser: str = "chrome") -> None:
    """Open a web address in Chrome when it is installed, otherwise in the default browser."""
    if config.MOCK_MODE:
        return
    if browser == "chrome":
        exe = find_chrome()
        if exe:
            subprocess.Popen([exe, url])
            return
    webbrowser.open(url)


class Agent:
    name: str = "Base"
    ACTIONS: frozenset[str] = frozenset()

    def plan(self, request: str, context: dict) -> list[dict]:
        """Hook for agent-local decomposition. The Planner currently owns decomposition."""
        return []

    def execute(self, action: str, params: dict, context: dict) -> Result:
        if action not in self.ACTIONS:
            return Result(False, f"{self.name} agent cannot perform '{action}'")
        try:
            return getattr(self, f"do_{action}")(params, context)
        except Exception as exc:  # an agent failure must never crash the orchestrator
            return Result(False, f"{self.name} agent error: {exc}")

    def report(self, action: str, result: Result) -> str:
        return result.message
