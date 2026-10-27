"""Planner Agent: turns any request into ordered sub-tasks (FR-6 to FR-10).

The local model reads the request and chooses from the tool catalogue below. Its answer is checked
against that catalogue before anything runs. If the model is unavailable, a few rules handle the
most common phrasings so FLOW still works offline.
"""
from __future__ import annotations

import json
import re

from flow import config, llm
from flow.agents.assistant_agent import AssistantAgent
from flow.agents.coding_agent import CodingAgent
from flow.agents.system_agent import APP_ALIASES, BROWSER_NAMES, VSCODE_NAMES, SystemAgent, find_app
from flow.agents.web_agent import WebAgent

AGENT_ACTIONS = {
    "System": SystemAgent.ACTIONS,
    "Coding": CodingAgent.ACTIONS,
    "Web": WebAgent.ACTIONS,
    "Assistant": AssistantAgent.ACTIONS,
}

TOOL_DOCS = {
    "System.open_app": "open an installed program, Start menu item or Windows settings page by name. args: name",
    "System.open_path": "open a file or folder in Explorer or its default program. args: path",
    "System.create_folder": "create a folder in the working folder. args: name or path",
    "System.create_file": "create a file with optional content. args: path, content",
    "System.write_file": "write text to a file, asking before it replaces an existing file. args: path, content",
    "System.read_file": "read a text file and return its text. args: path",
    "System.list_dir": "list the items in a folder. args: path",
    "System.copy": "copy a file or folder, asking before overwriting. args: src, dst",
    "System.move": "move or rename a file or folder (always asks first). args: src, dst",
    "System.delete": "delete a file or folder (always asks first). args: path",
    "System.open_in_vscode": "open the current project folder in VS Code. no args",
    "System.type_text": "type text into a window that is already open. args: text, window",
    "System.send_keys": "press a keyboard shortcut in a window. args: keys (for example ctrl+s), window",
    "System.focus_window": "bring an open window to the front by part of its title. args: title",
    "System.run_shell": "run a PowerShell command (the user sees and approves it first). args: command",
    "System.wait": "pause for a number of seconds, at most 30. args: seconds",
    "Coding.build_project": "create the code for a new project in the current folder. args: description, language (python or javascript)",
    "Coding.write_code": "write code for a description into the current Python or JavaScript file. args: description",
    "Coding.run_program": "run the current program after the user approves its source. no args",
    "Coding.fix_program": "try one automatic fix of the current program. no args",
    "Coding.git_init": "start a Git repository in the current project. no args",
    "Coding.git_commit": "commit the changes in the current project. args: message",
    "Web.open_url": "open a web address in the default browser. args: url (a full https address)",
    "Web.search": "search the web. args: query",
    "Web.play_media": "find a song or video on YouTube and play the best match. args: query",
    "Web.media_control": "pause, resume or skip playback in the browser. args: command (pause, resume or next)",
    "Assistant.answer": "answer a question or explain something in text. args: text",
}

EXAMPLES = [
    ("make a calculator",
     '{"steps":[{"agent":"System","action":"create_folder","parameters":{"name":"calculator"}},'
     '{"agent":"System","action":"open_in_vscode","parameters":{}},'
     '{"agent":"Coding","action":"build_project","parameters":{"description":"calculator","language":"python"}},'
     '{"agent":"Coding","action":"run_program","parameters":{}}]}'),
    ("open gmail",
     '{"steps":[{"agent":"Web","action":"open_url","parameters":{"url":"https://mail.google.com"}}]}'),
    ("open file explorer",
     '{"steps":[{"agent":"System","action":"open_app","parameters":{"name":"file explorer"}}]}'),
    ("type hello in notepad",
     '{"steps":[{"agent":"System","action":"type_text","parameters":{"text":"hello","window":"notepad"}}]}'),
    ("play shape of you",
     '{"steps":[{"agent":"Web","action":"play_media","parameters":{"query":"shape of you"}}]}'),
    ("what is 12 times 7",
     '{"steps":[{"agent":"Assistant","action":"answer","parameters":{"text":"What is 12 times 7?"}}]}'),
]

# Things that are not programs, so "make a ..." should not start a project for them
NOT_A_PROJECT = re.compile(r"\b(file|folder|website|web ?page|page|site|presentation|slides?|document|"
                           r"poster|report|essay|video|song|playlist|email|resume|letter)\b")

LANGUAGE_WORDS = {"python", "javascript", "js", "node", "a", "an", "the", "simple", "basic", "small"}
GENERIC_WRITE = {"it", "the code", "code", "the program", "the file", "this"}
CLAUSE_SPLIT = re.compile(
    r",|\s+then\s+|\s+and\s+(?=(?:open|make|build|play|search|launch|start|press|pause|resume|next|"
    r"commit|create|init|write|generate|save|run|execute|type|focus|delete|copy|move)\b)"
)


class Unsupported(Exception):
    pass


def _catalog() -> str:
    lines = []
    for agent, actions in AGENT_ACTIONS.items():
        for action in sorted(actions):
            doc = TOOL_DOCS.get(f"{agent}.{action}")
            if doc:
                lines.append(f"- {agent}.{action}: {doc}")
    return "\n".join(lines)


def build_prompt(command: str, previous_error: str | None = None) -> str:
    rules = (
        "You are FLOW's planner for a Windows computer. Turn the user's request into the smallest ordered "
        "list of steps that does it. Reply with JSON only, in the form "
        '{"steps": [{"agent": "...", "action": "...", "parameters": {...}}]}.\n'
        "Rules:\n"
        "- Use only the actions listed below. Never invent actions or parameters.\n"
        "- Use at most 10 steps. Never set \"confirmed\".\n"
        "- \"make a <thing>\" means create a new project (create_folder, open_in_vscode, build_project, run_program).\n"
        "- \"open <program>\" means open_app. \"open <website>\" means open_url with a full https address.\n"
        "- Questions and explanations use Assistant.answer.\n"
        "- If the request cannot be done, return {\"steps\": []}.\n"
    )
    text = (rules + "\nActions:\n" + _catalog() + "\n\nExamples:\n"
            + "\n".join(f"Request: {req}\nJSON: {js}" for req, js in EXAMPLES)
            + f"\n\nRequest: {command}\nJSON:")
    if previous_error:
        text = f"Your previous answer was rejected because {previous_error}. Reply with valid JSON only.\n\n" + text
    return text


def _step(agent: str, action: str, params: dict) -> dict:
    return {"agent": agent, "action": action, "parameters": params}


def _validate(data) -> list[dict] | None:
    """Check model output against the action catalogue. Strips any 'confirmed' flag (S-11)."""
    steps = data.get("steps") if isinstance(data, dict) else None
    if not isinstance(steps, list) or not steps or len(steps) > config.MAX_SUBTASKS:
        return None
    clean = []
    for s in steps:
        if not isinstance(s, dict):
            return None
        agent, action, params = s.get("agent"), s.get("action"), s.get("parameters", {})
        if agent not in AGENT_ACTIONS or action not in AGENT_ACTIONS[agent] or not isinstance(params, dict):
            return None
        clean.append(_step(agent, action, {k: v for k, v in params.items() if k != "confirmed"}))
    return clean


# ----- offline rules: used only when the model cannot answer -----

def _slug(text: str) -> str:
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in LANGUAGE_WORDS]
    return "-".join(words)[:40].strip("-") or "project"


def _project_steps(desc: str) -> list[dict]:
    language = "javascript" if re.search(r"\b(javascript|js|node)\b", desc) else "python"
    return [
        _step("System", "create_folder", {"name": _slug(desc)}),
        _step("System", "open_in_vscode", {}),
        _step("Coding", "build_project", {"description": desc, "language": language}),
        _step("Coding", "run_program", {}),
    ]


def _clause_steps(clause: str) -> list[dict]:
    if m := re.fullmatch(r"(?:create|make)\s+(?:a\s+|an\s+)?(?:(python|javascript|js|text)\s+)?file\s+(?:called|named)\s+([\w.\-]+)(?:\s+(?:on|in)\s+(?:the\s+)?desktop)?", clause):
        kind, name = m.group(1), m.group(2)
        ext = {"javascript": ".js", "js": ".js", "text": ".txt", "python": ".py"}.get(kind or "", "")
        path = name if "." in name or not ext else name + ext
        return [_step("System", "create_file", {"path": path, "content": ""})]
    if re.search(r"\b(?:init|initiali[sz]e|create)\s+(?:a\s+)?git\b", clause):
        return [_step("Coding", "git_init", {})]
    if re.fullmatch(r"commit(?:\s+(?:the\s+)?changes)?", clause):
        return [_step("Coding", "git_commit", {"message": "FLOW commit"})]
    if re.fullmatch(r"(?:run|execute)(?:\s+(?:it|the program|the code|the file|this))?", clause):
        return [_step("Coding", "run_program", {})]
    if re.fullmatch(r"save(?:\s+(?:it|the file|the code))?", clause):
        return []  # files are saved as they are written
    if m := re.fullmatch(r"(?:write|generate)\s+(?:a\s+|an\s+|some\s+)?(.+)", clause):
        desc = m.group(1).strip()
        if desc in GENERIC_WRITE:
            desc = "a small program"
        return [_step("Coding", "write_code", {"description": desc})]
    if m := re.fullmatch(r"press\s+(.+?)\s+in\s+(.+)", clause):
        return [_step("System", "send_keys", {"keys": "+".join(m.group(1).split()), "window": m.group(2)})]
    if m := re.fullmatch(r"open\s+(https?://\S+)", clause):
        return [_step("Web", "open_url", {"url": m.group(1)})]
    if m := re.fullmatch(r"(?:open|launch|start)\s+(?:the\s+)?(.+)", clause):
        name = m.group(1).strip()
        if _is_known_program(name):
            return [_step("System", "open_app", {"name": name})]
        # not a program on this computer: falls through so the model can open it (for example a website)
    if m := re.fullmatch(r"(?:make|build)\s+(?:a|an|the)?\s*(.+)", clause):
        if not NOT_A_PROJECT.search(m.group(1)):
            return _project_steps(m.group(1))
    if m := re.fullmatch(r"(pause|resume)(?:\s+(?:the\s+)?(?:music|song|video|track))?", clause):
        return [_step("Web", "media_control", {"command": m.group(1)})]
    if re.fullmatch(r"next(?:\s+(?:song|track|video))?", clause):
        return [_step("Web", "media_control", {"command": "next"})]
    if m := re.fullmatch(r"play\s+(.+)", clause):
        return [_step("Web", "play_media", {"query": m.group(1)})]
    if m := re.fullmatch(r"(?:search(?: for)?|google)\s+(.+)", clause):
        return [_step("Web", "search", {"query": m.group(1)})]
    raise Unsupported(
        "I can't handle that without the local AI model. Start Ollama and try again, or use a simpler command."
    )


def _is_known_program(name: str) -> bool:
    key = name.lower().strip()
    if key in VSCODE_NAMES or key in BROWSER_NAMES or key in APP_ALIASES:
        return True
    return find_app(key) is not None


def _rule_plan(command: str) -> list[dict]:
    steps: list[dict] = []
    for raw in CLAUSE_SPLIT.split(command.lower()):
        if raw.strip():
            steps.extend(_clause_steps(raw.strip()))
    deduped = []
    for step in steps:  # "make X and run it" already ends with a run step
        if deduped and step["action"] == "run_program" and deduped[-1]["action"] == "run_program":
            continue
        deduped.append(step)
    if not deduped or len(deduped) > config.MAX_SUBTASKS:
        raise Unsupported("The request could not be turned into a valid plan of up to 10 steps.")
    return deduped


def plan(command: str) -> list[dict]:
    """Clear requests use fixed rules, which cannot misread them. Anything else goes to the model."""
    try:
        return _rule_plan(command)
    except Unsupported as rule_error:
        if config.MOCK_MODE:
            raise
        error = None
        for _ in range(2):  # one retry, with the rejection reason in the prompt
            try:
                raw = llm.generate(build_prompt(command, error), system="You are FLOW's planner. Reply with JSON only.",
                                   json_mode=True)
                steps = _validate(json.loads(raw))
                if steps:
                    return steps
                error = "the plan was empty or used an action that does not exist"
            except Exception as exc:
                error = str(exc)
                break  # the model is unreachable, so retrying will not help
        raise rule_error
