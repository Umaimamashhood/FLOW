"""Common agent interface: plan, execute, report (SRS 4.3.4)."""
from __future__ import annotations

import webbrowser
from dataclasses import dataclass, field
from typing import Any

from flow import config


@dataclass
class Result:
    ok: bool
    message: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    needs_confirmation: bool = False


def open_url(url: str) -> None:
    if config.MOCK_MODE:
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
