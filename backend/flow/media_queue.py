"""Media links waiting for the desktop player window to open them."""
from __future__ import annotations

import threading

_lock = threading.Lock()
_pending: list[str] = []


def queue(url: str) -> None:
    with _lock:
        _pending.append(url)


def pop_all() -> list[str]:
    with _lock:
        items = list(_pending)
        _pending.clear()
        return items
