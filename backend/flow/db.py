"""SQLite persistence with versioned migrations (SRS Chapter 5, item 1)."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from flow import config

MIGRATIONS: list[tuple[int, str]] = [
    (1, """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        command     TEXT NOT NULL,
        input_mode  TEXT NOT NULL DEFAULT 'text',
        status      TEXT NOT NULL,
        outcome     TEXT,
        error       TEXT,
        created_at  TEXT NOT NULL,
        finished_at TEXT
    );
    CREATE TABLE IF NOT EXISTS subtasks (
        subtask_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id     INTEGER NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        sequence_no INTEGER NOT NULL,
        agent       TEXT NOT NULL,
        action      TEXT NOT NULL,
        parameters  TEXT NOT NULL DEFAULT '{}',
        status      TEXT NOT NULL DEFAULT 'Pending',
        result      TEXT
    );
    CREATE TABLE IF NOT EXISTS action_log (
        log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id    INTEGER NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        subtask_id INTEGER REFERENCES subtasks(subtask_id) ON DELETE CASCADE,
        timestamp  TEXT NOT NULL,
        event      TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS preferences (
        key   TEXT PRIMARY KEY,
        value TEXT
    );
    """),
    (2, "CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);"),
]

INTERRUPTED = ("Planning", "Executing", "Awaiting Confirmation", "Paused")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Apply pending migrations and fail tasks interrupted by an earlier shutdown (SRS 4.3.1)."""
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as c:
        c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        current = c.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()[0]
    for version, sql in MIGRATIONS:
        if version > current:
            with connect() as c:
                c.executescript(sql)
                c.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))
    placeholders = ",".join("?" * len(INTERRUPTED))
    with connect() as c:
        c.execute(
            f"UPDATE tasks SET status='Failed', outcome='Failed', error='interrupted', finished_at=? "
            f"WHERE status IN ({placeholders})",
            (_now(), *INTERRUPTED),
        )


def schema_version() -> int:
    with connect() as c:
        return c.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()[0]


def create_task(command: str, mode: str) -> int:
    with connect() as c:
        cur = c.execute(
            "INSERT INTO tasks(command, input_mode, status, created_at) VALUES (?,?,?,?)",
            (command, mode, "Planning", _now()),
        )
        return cur.lastrowid


def get_task_status(task_id: int) -> str | None:
    with connect() as c:
        row = c.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        return row["status"] if row else None


def set_task_status(task_id: int, status: str, outcome: str | None = None, error: str | None = None) -> None:
    finished = _now() if status in ("Completed", "Failed") else None
    with connect() as c:
        c.execute(
            "UPDATE tasks SET status=?, outcome=COALESCE(?, outcome), error=COALESCE(?, error), "
            "finished_at=COALESCE(?, finished_at) WHERE task_id=?",
            (status, outcome, error, finished, task_id),
        )


def add_subtask(task_id: int, seq: int, agent: str, action: str, params: dict) -> int:
    with connect() as c:
        cur = c.execute(
            "INSERT INTO subtasks(task_id, sequence_no, agent, action, parameters) VALUES (?,?,?,?,?)",
            (task_id, seq, agent, action, json.dumps(params)),
        )
        return cur.lastrowid


def set_subtask(subtask_id: int, status: str, result: str | None = None) -> None:
    with connect() as c:
        c.execute(
            "UPDATE subtasks SET status=?, result=COALESCE(?, result) WHERE subtask_id=?",
            (status, result, subtask_id),
        )


def log(task_id: int, event: str, subtask_id: int | None = None) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO action_log(task_id, subtask_id, timestamp, event) VALUES (?,?,?,?)",
            (task_id, subtask_id, _now(), event),
        )


def get_task(task_id: int) -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            return None
        task = dict(row)
        subs = c.execute(
            "SELECT * FROM subtasks WHERE task_id=? ORDER BY sequence_no", (task_id,)
        ).fetchall()
        task["subtasks"] = [{**dict(s), "parameters": json.loads(s["parameters"])} for s in subs]
        logs = c.execute(
            "SELECT timestamp, event, subtask_id FROM action_log WHERE task_id=? ORDER BY log_id",
            (task_id,),
        ).fetchall()
        task["log"] = [dict(r) for r in logs]
        return task


def list_tasks(search: str = "", page: int = 1, page_size: int = 50) -> list[dict]:
    """Newest first; case-insensitive substring match on the command (FR-38)."""
    with connect() as c:
        rows = c.execute(
            "SELECT task_id, command, status, outcome, error, created_at, finished_at FROM tasks "
            "WHERE lower(command) LIKE ? ORDER BY created_at DESC, task_id DESC LIMIT ? OFFSET ?",
            (f"%{search.lower()}%", page_size, (page - 1) * page_size),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_task(task_id: int) -> bool:
    with connect() as c:
        return c.execute("DELETE FROM tasks WHERE task_id=?", (task_id,)).rowcount > 0


def clear_history() -> None:
    with connect() as c:
        c.execute("DELETE FROM tasks")


def export_all() -> dict:
    with connect() as c:
        ids = [r["task_id"] for r in c.execute("SELECT task_id FROM tasks ORDER BY task_id")]
    return {"schema_version": schema_version(), "exported_at": _now(),
            "tasks": [get_task(i) for i in ids]}


def all_prefs() -> dict[str, str]:
    with connect() as c:
        return {r["key"]: r["value"] for r in c.execute("SELECT key, value FROM preferences")}


def set_pref(key: str, value: str) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO preferences(key, value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
