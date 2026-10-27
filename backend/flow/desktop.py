"""Keyboard, window and media control through PyAutoGUI, with focus checks (FR-14, FR-30, S-12, S-13)."""
from __future__ import annotations

import string

from flow import config

NAMED_KEYS = {"ctrl", "shift", "alt", "win", "enter", "tab", "esc", "space", "backspace",
              "delete", "up", "down", "left", "right", "home", "end", "pageup", "pagedown"}
ALLOWED_KEYS = NAMED_KEYS | set(string.ascii_lowercase) | set(string.digits) | {f"f{i}" for i in range(1, 13)}


def parse_hotkey(spec: str) -> list[str]:
    keys = [k.strip().lower() for k in str(spec).split("+") if k.strip()]
    if not keys or len(keys) > 4:
        raise ValueError("give one to four keys, for example ctrl+s")
    bad = [k for k in keys if k not in ALLOWED_KEYS]
    if bad:
        raise ValueError(f"unsupported key: {bad[0]}")
    return keys


def _load_backends():
    try:
        import pyautogui  # optional dependency
        import pygetwindow  # optional dependency
    except Exception as exc:
        raise ImportError(str(exc)) from exc
    pyautogui.FAILSAFE = True  # S-12: moving the mouse to a corner aborts input
    return pygetwindow, pyautogui


def _active_title(gw) -> str:
    try:
        active = gw.getActiveWindow()
        return (active.title or "") if active else ""
    except Exception:
        return ""


def send_hotkey(window: str, keys: list[str]) -> tuple[bool, str]:
    if config.MOCK_MODE:
        return True, f"(mock) would send {'+'.join(keys)} to '{window}'"
    try:
        gw, pg = _load_backends()
    except ImportError:
        return False, "Keyboard control needs PyAutoGUI and PyGetWindow installed"
    title = _active_title(gw)
    if window.lower() not in title.lower():  # S-13
        return False, f"'{window}' is not the focused window, so no keys were sent"
    pg.hotkey(*keys)
    return True, f"Sent {'+'.join(keys)} to {title}"


def send_text(window: str, text: str) -> tuple[bool, str]:
    if config.MOCK_MODE:
        return True, f"(mock) would type into '{window}'"
    try:
        gw, pg = _load_backends()
    except ImportError:
        return False, "Typing needs PyAutoGUI and PyGetWindow installed"
    title = _active_title(gw)
    if window.lower() not in title.lower():
        return False, f"'{window}' is not the focused window, so nothing was typed"
    pg.write(text, interval=0.02)
    return True, f"Typed into {title}"


def focus_window(title_part: str) -> tuple[bool, str]:
    if config.MOCK_MODE:
        return True, f"(mock) would bring '{title_part}' to the front"
    try:
        gw, _ = _load_backends()
    except ImportError:
        return False, "Window control needs PyGetWindow installed"
    matches = gw.getWindowsWithTitle(title_part)
    if not matches:
        return False, f"No open window has '{title_part}' in its title"
    try:
        matches[0].activate()
    except Exception as exc:
        return False, f"Could not bring '{title_part}' to the front: {exc}"
    return True, f"Brought '{matches[0].title}' to the front"


def media_key(name: str) -> tuple[bool, str]:
    if config.MOCK_MODE:
        return True, f"(mock) media key '{name}'"
    try:
        _, pg = _load_backends()
    except ImportError:
        return False, "Media control needs PyAutoGUI installed"
    pg.press(name)
    return True, "Media key sent"
