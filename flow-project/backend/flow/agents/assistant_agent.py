"""Assistant Agent: answers questions and explains things in plain text."""
from __future__ import annotations

from flow import config, llm
from flow.agents.base import Agent, Result

SYSTEM = "You are FLOW, a helpful desktop assistant. Answer briefly and clearly in plain text."


class AssistantAgent(Agent):
    name = "Assistant"
    ACTIONS = frozenset({"answer"})

    def do_answer(self, params: dict, ctx: dict) -> Result:
        text = str(params.get("text", "")).strip()
        if not text:
            return Result(False, "There is no question to answer")
        if config.MOCK_MODE:
            return Result(True, f"(mock) answer to: {text}")
        answer = llm.generate(text, system=SYSTEM).strip()
        return Result(True, answer or "I don't have an answer for that.")
