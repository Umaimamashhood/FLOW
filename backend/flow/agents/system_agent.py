"""System Agent: programs, files, folders, windows, keyboard and shell (FR-11 to FR-16)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from flow import config, desktop
from flow.agents.base import Agent, Result, open_url

# Friendly names that do not match a program's file name. Data, not logic: anything else is searched for.
APP_ALIASES = {
    "vs code": "code", "vscode": "code", "visual studio code": "code",
    "calculator": "calc", "calc": "calc", "paint": "mspaint",
    "file explorer": "explorer", "explorer": "explorer", "file manager": "explorer",
    "terminal": "wt", "command prompt": "cmd", "cmd": "cmd", "powershell": "powershell",
    "task manager": "taskmgr", "settings": "ms-settings:",
}
BROWSER_NAMES = {"browser", "web browser", "default browser"}
VSCODE_NAMES = {"vs code", "vscode", "visual studio code", "code"}
NAME_RE = re.compile(r"[a-z0-9 .:\-]{1,80}")
MAX_PATH_LEN = 260
RISKY_SUFFIXES = {".exe", ".bat", ".cmd", ".ps1", ".msi", ".com", ".scr", ".lnk", ".vbs", ".js"}


def safe_path(raw: str | None, base: Path | None = None) -> Path:
    """Resolve a path and require it to lie inside a permitted folder (S-17, S-22). Used for changes."""
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw or len(raw) > MAX_PATH_LEN:
        raise ValueError("invalid path")
    p = Path(os.path.expandvars(raw.strip())).expanduser()
    if not p.is_absolute():
        p = (base or config.PROJECTS_DIR) / p
    p = p.resolve()
    for allowed in config.ALLOWED_DIRS:
        root = Path(allowed).resolve()
        if p == root or root in p.parents:
            return p
    raise PermissionError(f"that location is outside the permitted folders: {p}")


def find_vscode() -> str | None:
    exe = shutil.which("code")
    if exe:
        return exe
    for candidate in (
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Microsoft VS Code" / "Code.exe",
    ):
        if candidate.is_file():
            return str(candidate)
    return None


def _app_paths_lookup(exe_name: str) -> str | None:
    """Windows registers installed programs under App Paths. Read that registry key."""
    try:
        import winreg
    except ImportError:
        return None
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}") as key:
                value, _ = winreg.QueryValueEx(key, "")
                if value and Path(value).exists():
                    return value
        except OSError:
            continue
    return None


def start_menu_roots() -> list[Path]:
    roots = []
    for var in ("APPDATA", "PROGRAMDATA"):
        base = os.environ.get(var)
        if base:
            roots.append(Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    return [r for r in roots if r.exists()]


def find_start_menu_shortcut(name: str) -> Path | None:
    """Find a Start menu shortcut whose name contains every word asked for."""
    words = re.findall(r"[a-z0-9]+", name.lower())
    if not words:
        return None
    best = None
    for root in start_menu_roots():
        for lnk in root.rglob("*.lnk"):
            stem = lnk.stem.lower()
            if all(w in stem for w in words) and (best is None or len(stem) < len(best.stem.lower())):
                best = lnk
    return best


def find_app(name: str) -> str | None:
    alias = APP_ALIASES.get(name, name)
    exe = shutil.which(alias) or shutil.which(alias + ".exe")
    if exe:
        return exe
    if os.name == "nt":
        registered = _app_paths_lookup(alias if alias.endswith(".exe") else alias + ".exe")
        if registered:
            return registered
    shortcut = find_start_menu_shortcut(name)
    return str(shortcut) if shortcut else None


def _open_target(target: str) -> None:
    if config.MOCK_MODE:
        return
    if os.name == "nt":
        os.startfile(target)  # opens programs, shortcuts, files and folders the way Windows does
    else:
        subprocess.Popen(["xdg-open", target])


def _spawn(args: list[str]) -> None:
    if config.MOCK_MODE:
        return
    if os.name == "nt" and args[0].lower().endswith((".cmd", ".bat")):
        args = ["cmd", "/c", *args]
    subprocess.Popen(args)


class SystemAgent(Agent):
    name = "System"
    ACTIONS = frozenset({
        "open_app", "launch_app", "open_path", "create_folder", "create_file", "write_file",
        "read_file", "list_dir", "copy", "move", "delete", "open_in_vscode",
        "send_keys", "type_text", "focus_window", "run_shell", "wait",
    })

    def _base(self, ctx: dict) -> Path:
        return Path(ctx["project_path"]) if ctx.get("project_path") else config.PROJECTS_DIR

    # ----- programs and windows -----
    def do_open_app(self, params: dict, ctx: dict) -> Result:
        name = str(params.get("name", "")).strip().lower()
        if not name or not NAME_RE.fullmatch(name):
            return Result(False, "Tell me which program to open")
        if name in BROWSER_NAMES:
            open_url("https://www.google.com")
            return Result(True, "Opened the default browser")
        if name in VSCODE_NAMES:
            exe = find_vscode()
            if exe is None:
                return Result(False, "VS Code was not found on this computer")
            _spawn([exe])
            return Result(True, "Opened VS Code")
        if config.MOCK_MODE:
            return Result(True, f"(mock) would open {name}")
        target = find_app(name)
        if target is None:
            return Result(False, f"I couldn't find '{name}' on this computer. "
                                 "Tell me where it is, or ask me to open its website instead.")
        _open_target(target)
        return Result(True, f"Opened {name}")

    def do_launch_app(self, params: dict, ctx: dict) -> Result:
        return self.do_open_app(params, ctx)

    def do_open_path(self, params: dict, ctx: dict) -> Result:
        """Opening does not change anything, so any existing file or folder can be opened."""
        raw = str(params.get("path", "")).strip()
        if not raw or "\x00" in raw or len(raw) > MAX_PATH_LEN:
            return Result(False, "Give the file or folder to open")
        p = Path(os.path.expandvars(raw)).expanduser()
        if not p.is_absolute():
            p = self._base(ctx) / p
        if not p.exists():
            return Result(False, f"{p} does not exist")
        if p.suffix.lower() in RISKY_SUFFIXES and not params.get("confirmed"):
            return Result(False, f"Open or run {p.name}? Only do this if you trust it.", needs_confirmation=True)
        _open_target(str(p))
        return Result(True, f"Opened {p}")

    def do_open_in_vscode(self, params: dict, ctx: dict) -> Result:
        exe = find_vscode()
        if exe is None:  # the project is still usable, so this is a notice rather than a failure
            return Result(True, "VS Code was not found. The project is saved and can be opened manually.")
        if not ctx.get("project_path"):
            _spawn([exe])
            return Result(True, "Opened VS Code")
        folder = safe_path(ctx["project_path"])
        _spawn([exe, str(folder)])
        return Result(True, f"Opened {folder} in VS Code")

    def do_send_keys(self, params: dict, ctx: dict) -> Result:
        window = str(params.get("window", "")).strip()
        if not window or len(window) > 100:
            return Result(False, "Name the window that should receive the keys")
        try:
            keys = desktop.parse_hotkey(str(params.get("keys", "")))
        except ValueError as exc:
            return Result(False, str(exc))
        ok, message = desktop.send_hotkey(window, keys)
        return Result(ok, message)

    def do_type_text(self, params: dict, ctx: dict) -> Result:
        window = str(params.get("window", "")).strip()
        text = str(params.get("text", ""))
        if not window or not text or len(text) > 2000:
            return Result(False, "Give the text to type and the window to type it into")
        ok, message = desktop.send_text(window, text)
        return Result(ok, message)

    def do_focus_window(self, params: dict, ctx: dict) -> Result:
        title = str(params.get("title", "")).strip()
        if not title or len(title) > 100:
            return Result(False, "Give part of the window title to bring forward")
        ok, message = desktop.focus_window(title)
        return Result(ok, message)

    def do_run_shell(self, params: dict, ctx: dict) -> Result:
        command = str(params.get("command", "")).strip()
        if not command or len(command) > 500 or "\x00" in command:
            return Result(False, "Give a command to run")
        if not params.get("confirmed"):  # the user sees the exact command before it runs
            return Result(False, f"Run this command in PowerShell?\n\n{command}", needs_confirmation=True)
        if config.MOCK_MODE:
            return Result(True, f"(mock) would run: {command}")
        shell = ["powershell", "-NoProfile", "-Command", command] if os.name == "nt" else ["sh", "-c", command]
        try:
            proc = subprocess.run(shell, cwd=config.PROJECTS_DIR, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return Result(False, "The command was stopped after 60 seconds")
        output = (proc.stdout + proc.stderr).strip()[:2000] or "(no output)"
        return Result(proc.returncode == 0, output, {"exit_code": proc.returncode})

    def do_wait(self, params: dict, ctx: dict) -> Result:
        try:
            seconds = max(0.0, min(float(params.get("seconds", 1)), 30.0))
        except (TypeError, ValueError):
            return Result(False, "Give the number of seconds to wait")
        if not config.MOCK_MODE:
            time.sleep(seconds)
        return Result(True, f"Waited {seconds:g} seconds")

    # ----- files and folders -----
    def do_create_folder(self, params: dict, ctx: dict) -> Result:
        target = safe_path(params.get("path") or params.get("name"), base=config.PROJECTS_DIR)
        final, n = target, 2
        while final.exists():  # name clash: add a suffix rather than overwrite
            final = target.with_name(f"{target.name}-{n}")
            n += 1
        final.mkdir(parents=True)
        return Result(True, f"Created folder {final}", {"project_path": str(final)})

    def do_create_file(self, params: dict, ctx: dict) -> Result:
        p = safe_path(params.get("path") or params.get("name"), base=self._base(ctx))
        if p.exists() and not params.get("confirmed"):
            return Result(False, f"{p} already exists. Confirm to overwrite it.", needs_confirmation=True)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(params.get("content", "")), encoding="utf-8")
        output = {"file_path": str(p)}
        if p.suffix == ".py":
            output["main_file"] = str(p)  # the most recently written Python file is the program
        return Result(True, f"Wrote {p}", output)

    def do_write_file(self, params: dict, ctx: dict) -> Result:
        return self.do_create_file(params, ctx)

    def do_read_file(self, params: dict, ctx: dict) -> Result:
        p = safe_path(params.get("path"), base=self._base(ctx))
        if not p.is_file():
            return Result(False, f"{p} is not a file")
        text = p.read_text(encoding="utf-8", errors="replace")
        shown = text[:4000] + ("\n...(truncated)" if len(text) > 4000 else "")
        return Result(True, shown or "(empty file)", {"file_path": str(p)})

    def do_list_dir(self, params: dict, ctx: dict) -> Result:
        p = safe_path(params.get("path") or str(config.PROJECTS_DIR), base=self._base(ctx))
        items = sorted(x.name for x in p.iterdir())
        return Result(True, ", ".join(items) or "(empty)", {"items": items})

    def do_copy(self, params: dict, ctx: dict) -> Result:
        base = self._base(ctx)
        src = safe_path(params.get("src"), base=base)
        dst = safe_path(params.get("dst"), base=base)
        if not src.exists():
            return Result(False, f"{src} does not exist")
        if dst.exists() and not params.get("confirmed"):
            return Result(False, f"{dst} already exists. Confirm to overwrite it.", needs_confirmation=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return Result(True, f"Copied {src} to {dst}", {"file_path": str(dst)})

    def do_move(self, params: dict, ctx: dict) -> Result:
        src = safe_path(params.get("src"), base=self._base(ctx))
        dst = safe_path(params.get("dst"), base=self._base(ctx))
        if not src.exists():
            return Result(False, f"{src} does not exist")
        if not params.get("confirmed"):  # moves are always confirmed (FR-15)
            return Result(False, f"Move {src} to {dst}?", needs_confirmation=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return Result(True, f"Moved {src} to {dst}")

    def do_delete(self, params: dict, ctx: dict) -> Result:
        p = safe_path(params.get("path"), base=self._base(ctx))
        if any(p == Path(a).resolve() for a in config.ALLOWED_DIRS):
            return Result(False, "Refusing to delete a top-level permitted folder")
        if not params.get("confirmed"):
            return Result(False, f"Delete {p}? This cannot be undone.", needs_confirmation=True)
        if not p.exists():
            return Result(False, f"{p} does not exist")
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return Result(True, f"Deleted {p}")
