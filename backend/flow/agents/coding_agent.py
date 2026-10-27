"""Coding Agent: generates, writes, fixes, runs and version-controls code (FR-17 to FR-25)."""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from flow import config, llm
from flow.agents.base import Agent, Result
from flow.agents.system_agent import safe_path

MOCK_TEMPLATES = {
    "python": 'print("Hello from FLOW (mock project)")\n',
    "javascript": 'console.log("Hello from FLOW (mock project)");\n',
}

# A known-good program for the most common request. A small local model writes weaker code,
# so this one is used directly and does not depend on the model.
CALCULATOR_TEMPLATE = r'''import tkinter as tk


def evaluate(expression):
    allowed = set("0123456789+-*/.() ")
    if not expression or len(expression) > 60 or not set(expression) <= allowed:
        return "Error"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception:
        return "Error"


class Calculator:
    def __init__(self, root):
        self.root = root
        root.title("Calculator")
        root.resizable(False, False)
        self.display = tk.Entry(root, font=("Segoe UI", 20), justify="right", bd=6)
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=6, pady=6)
        rows = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+"],
        ]
        for r, row in enumerate(rows, start=1):
            for c, label in enumerate(row):
                tk.Button(root, text=label, font=("Segoe UI", 16), width=4, height=2,
                          command=lambda value=label: self.press(value)).grid(row=r, column=c, sticky="nsew")
        tk.Button(root, text="C", font=("Segoe UI", 16), height=2,
                  command=self.clear).grid(row=5, column=0, columnspan=4, sticky="nsew")
        root.bind("<Return>", lambda event: self.press("="))

    def press(self, value):
        if value == "=":
            result = evaluate(self.display.get())
            self.clear()
            self.display.insert(0, result)
        else:
            self.display.insert("end", value)

    def clear(self):
        self.display.delete(0, "end")


if __name__ == "__main__":
    root = tk.Tk()
    Calculator(root)
    root.mainloop()
'''
GUI_IMPORT = re.compile(r"^\s*(?:import|from)\s+(tkinter|pygame|PyQt5|PyQt6|PySide6)\b", re.M)


def is_gui_program(source: str) -> bool:
    """Graphical programs open their own window and are not waited on (FR-23)."""
    return bool(GUI_IMPORT.search(source))


def strip_fences(text: str) -> str:
    match = re.search(r"```[a-zA-Z0-9]*\n(.*?)```", text, re.S)
    return (match.group(1) if match else text).strip() + "\n"


def python_syntax_error(code: str) -> str | None:
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return f"line {exc.lineno}: {exc.msg}"


def _git(folder: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.name=FLOW", "-c", "user.email=flow@localhost", *args],
        cwd=folder, capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip() or f"git {args[0]} failed")
    return proc.stdout.strip()


class CodingAgent(Agent):
    name = "Coding"
    ACTIONS = frozenset({"build_project", "write_code", "run_program", "fix_program", "git_init", "git_commit"})

    def _generate(self, description: str, language: str) -> str:
        if language == "python" and "calculator" in description.lower():
            return CALCULATOR_TEMPLATE
        if config.MOCK_MODE:
            return MOCK_TEMPLATES[language]
        system = f"You write complete, runnable {language} programs. Output only code."
        prompt = f"Write a {language} program that does the following: {description}"
        return strip_fences(llm.generate(prompt, system=system))

    def _fix(self, source: str, error: str, suffix: str) -> str:
        if config.MOCK_MODE:
            return MOCK_TEMPLATES["python" if suffix == ".py" else "javascript"]
        prompt = ("This program fails with the error below. Return the full corrected program only.\n\n"
                  f"Error:\n{error}\n\nProgram:\n{source}")
        return strip_fences(llm.generate(prompt, system="You fix bugs in small programs. Output only code."))

    def do_build_project(self, params: dict, ctx: dict) -> Result:
        if not ctx.get("project_path"):
            return Result(False, "No project folder was created")
        folder = safe_path(ctx["project_path"])
        language = str(params.get("language", "python")).lower()
        if language not in MOCK_TEMPLATES:
            return Result(False, f"Unsupported language '{language}'")
        description = str(params.get("description", "")).strip() or "a small program"
        code = self._generate(description, language)
        if language == "python":
            err = python_syntax_error(code)
            if err:
                return Result(False, f"Generated code failed the syntax check ({err})")
        main = folder / ("main.py" if language == "python" else "index.js")
        main.write_text(code, encoding="utf-8")
        (folder / "README.md").write_text(f"# {folder.name}\n\n{description}\n", encoding="utf-8")
        return Result(True, f"Wrote {main.name} and README.md", {"main_file": str(main)})

    def do_write_code(self, params: dict, ctx: dict) -> Result:
        """Write code into the Python or JavaScript file created earlier in the same request."""
        if not ctx.get("main_file"):
            return Result(False, "Create a Python or JavaScript file first, then ask me to write code")
        main = safe_path(ctx["main_file"])
        description = str(params.get("description", "")).strip() or "a small program"
        language = "javascript" if main.suffix == ".js" else "python"
        code = self._generate(description, language)
        if language == "python":
            err = python_syntax_error(code)
            if err:
                return Result(False, f"Generated code failed the syntax check ({err})")
        main.write_text(code, encoding="utf-8")
        return Result(True, f"Wrote code to {main.name}", {"main_file": str(main)})

    def do_fix_program(self, params: dict, ctx: dict) -> Result:
        main = safe_path(ctx.get("main_file"))
        source = main.read_text(encoding="utf-8")
        fixed = self._fix(source, ctx.get("last_error", ""), main.suffix)
        if main.suffix == ".py":
            err = python_syntax_error(fixed)
            if err:
                return Result(False, f"The suggested fix failed the syntax check ({err})")
        main.write_text(fixed, encoding="utf-8")
        return Result(True, f"Applied an automatic fix to {main.name}")

    def do_run_program(self, params: dict, ctx: dict) -> Result:
        if not ctx.get("main_file"):
            return Result(False, "There is no program to run")
        main = safe_path(ctx["main_file"])
        source = main.read_text(encoding="utf-8")
        if not params.get("confirmed"):  # S-14 and S-15: show the source first
            return Result(False, f"Run {main.name}? Review the source first:\n\n{source}",
                          needs_confirmation=True)
        is_py = main.suffix == ".py"
        gui = is_py and is_gui_program(source)
        if gui and config.MOCK_MODE:
            return Result(True, f"(mock) {main.name} would open in its own window", {"running": True})
        cmd = [sys.executable, str(main)] if is_py else ["node", str(main)]
        if gui:
            try:
                proc = subprocess.Popen(cmd, cwd=main.parent)
            except FileNotFoundError as exc:
                return Result(False, f"Runtime not found: {exc.filename}")
            return Result(True, f"{main.name} is running in its own window (process {proc.pid})",
                          {"running": True})
        try:
            proc = subprocess.Popen(cmd, cwd=main.parent, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
        except FileNotFoundError as exc:
            return Result(False, f"Runtime not found: {exc.filename}")
        cancel = ctx.get("_cancel")
        deadline = time.monotonic() + config.RUN_TIMEOUT
        while True:
            try:
                out, err = proc.communicate(timeout=0.2)  # short polls let abort act within 1 s (P-10)
                break
            except subprocess.TimeoutExpired:
                if cancel is not None and cancel.is_set():
                    proc.kill()
                    proc.communicate()
                    return Result(False, "Program stopped by abort", {"cancelled": True})
                if time.monotonic() > deadline:
                    proc.kill()
                    proc.communicate()
                    return Result(False, f"Program was stopped after {config.RUN_TIMEOUT} seconds",
                                  {"timed_out": True})
        output = (out + err).strip() or "(no output)"
        return Result(proc.returncode == 0, output, {"exit_code": proc.returncode})

    def do_git_init(self, params: dict, ctx: dict) -> Result:
        folder = safe_path(ctx.get("project_path") or params.get("path"))
        if shutil.which("git") is None:
            return Result(False, "Git is not installed or not on PATH")
        if (folder / ".git").exists():
            return Result(True, "This folder is already a Git repository")
        _git(folder, "init")
        _git(folder, "add", "-A")
        _git(folder, "commit", "--allow-empty", "-m", "Initial commit")
        return Result(True, f"Created a Git repository in {folder}")

    def do_git_commit(self, params: dict, ctx: dict) -> Result:
        folder = safe_path(ctx.get("project_path") or params.get("path"))
        if not (folder / ".git").exists():
            return Result(False, "This folder is not a Git repository")
        _git(folder, "add", "-A")
        if not _git(folder, "status", "--porcelain"):
            return Result(True, "Nothing to commit")
        _git(folder, "commit", "-m", str(params.get("message") or "FLOW commit"))
        return Result(True, "Committed the changes")
