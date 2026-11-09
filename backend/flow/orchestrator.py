"""Orchestrator: runs sub-tasks in a background thread with pause, resume, abort, confirmation
gates and one automatic fix attempt (FR-22, FR-32 to FR-34)."""
from __future__ import annotations

import threading

from flow import db, planner, settings, state, voice
from flow.agents.assistant_agent import AssistantAgent
from flow.agents.coding_agent import CodingAgent
from flow.agents.system_agent import SystemAgent
from flow.agents.web_agent import WebAgent

FILE_OPS = {"delete", "move", "create_file", "copy"}


class ConflictError(Exception):
    """The request does not fit the task's current state (HTTP 409)."""


def _step(agent: str, action: str, params: dict) -> dict:
    return {"agent": agent, "action": action, "parameters": params}


class _Run:
    def __init__(self, task_id: int, steps: list[dict], keep: bool) -> None:
        self.task_id = task_id
        self.steps = steps
        self.keep = keep
        self.idx = 0
        self.context: dict = {}
        self.cancel = threading.Event()
        self.context["_cancel"] = self.cancel
        self.resume = threading.Event()
        self.resume.set()
        self.decision = threading.Event()
        self.approved = False
        self.choice: int | None = None
        self.confirmed = False
        self.pending: dict = {}
        self.awaiting: dict | None = None
        self.fix_attempted = False
        self.last_message = ""


class Orchestrator:
    def __init__(self) -> None:
        self.agents = {a.name: a for a in (SystemAgent(), CodingAgent(), WebAgent(), AssistantAgent())}
        self._lock = threading.RLock()
        self._run: _Run | None = None
        self._thread: threading.Thread | None = None

    # ----- queries -----
    @property
    def active_task_id(self) -> int | None:
        with self._lock:
            return self._run.task_id if self._run else None

    def awaiting_info(self) -> dict | None:
        run = self._run
        return dict(run.awaiting) if run and run.awaiting else None

    def wait(self, timeout: float = 10.0) -> None:
        """Block until the current background run finishes (used by tests and scripts)."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    # ----- commands -----
    def submit(self, command: str, mode: str = "text") -> int:
        with self._lock:
            if self._run is not None:
                raise ConflictError("Another task is still running. Pause, abort or wait for it to finish.")
            keep = settings.get()["history_enabled"]
            task_id = db.create_task(command, mode)
            try:
                steps = planner.plan(command)
            except planner.Unsupported as exc:
                db.log(task_id, f"planning failed: {exc}")
                self._finish(task_id, "Failed", str(exc), keep)
                return task_id
            for seq, step in enumerate(steps, 1):
                step["id"] = db.add_subtask(task_id, seq, step["agent"], step["action"], step["parameters"])
            self._transition(task_id, "Executing")
            run = _Run(task_id, steps, keep)
            self._run = run
            self._thread = threading.Thread(target=self._execute, args=(run,), daemon=True)
            self._thread.start()
            return task_id

    def pause(self, task_id: int) -> None:
        with self._lock:
            run = self._require(task_id)
            if run.awaiting:
                raise ConflictError("The task is waiting for confirmation, so it cannot be paused.")
            self._transition(task_id, "Paused")
            run.resume.clear()

    def resume(self, task_id: int) -> None:
        with self._lock:
            run = self._require(task_id)
            self._transition(task_id, "Executing")
            run.resume.set()

    def abort(self, task_id: int | None = None) -> None:
        with self._lock:
            run = self._require(task_id) if task_id is not None else self._current()
            run.cancel.set()
            run.approved = False
            run.decision.set()
            run.resume.set()

    def confirm(self, task_id: int, approved: bool, choice: int | None = None) -> None:
        with self._lock:
            run = self._require(task_id)
            if not run.awaiting:
                raise ConflictError("The task is not waiting for confirmation.")
            run.approved = approved
            run.choice = choice
            run.decision.set()

    # ----- internals -----
    def _require(self, task_id: int) -> _Run:
        if self._run is None or self._run.task_id != task_id:
            raise ConflictError("That task is not running.")
        return self._run

    def _current(self) -> _Run:
        if self._run is None:
            raise ConflictError("No task is running.")
        return self._run

    def _transition(self, task_id: int, new: str, **fields) -> None:
        state.check_transition(db.get_task_status(task_id), new)
        db.set_task_status(task_id, new, **fields)

    def _finish(self, task_id: int, outcome: str, error: str | None, keep: bool) -> None:
        with self._lock:
            if db.get_task_status(task_id) in state.TERMINAL or db.get_task_status(task_id) is None:
                return
            status = "Completed" if outcome == "Completed" else "Failed"
            self._transition(task_id, status, outcome=outcome, error=error)
            if not keep:  # history is off: nothing stays in the database
                db.delete_task(task_id)

    def _execute(self, run: _Run) -> None:
        try:
            self._loop(run)
        except Exception as exc:
            self._finish(run.task_id, "Failed", f"internal error: {exc}", run.keep)
        finally:
            with self._lock:
                if self._run is run:
                    self._run = None

    def _auto_approved(self, action: str) -> bool:
        policy = settings.get()["confirmation_policy"]
        if policy == "Unattended":
            return action in FILE_OPS  # S-11: only when the user opted in
        if policy == "Confirm Destructive Only":
            return action == "create_file"  # overwrites only
        return False

    def _should_auto_fix(self, run: _Run, step: dict, result) -> bool:
        return (step["action"] == "run_program" and not run.fix_attempted
                and not result.output.get("timed_out") and not result.output.get("cancelled"))

    def _append_fix_steps(self, run: _Run) -> None:
        for step in (_step("Coding", "fix_program", {}), _step("Coding", "run_program", {})):
            step["id"] = db.add_subtask(run.task_id, len(run.steps) + 1, step["agent"], step["action"], step["parameters"])
            run.steps.append(step)
        db.log(run.task_id, "automatic fix: sending the error to the Coding Agent (one attempt)")

    def _abort_run(self, run: _Run, reason: str) -> None:
        for i, step in enumerate(run.steps[run.idx:], start=run.idx):
            db.set_subtask(step["id"], "Failed", reason if i == run.idx else "Not run")
        db.log(run.task_id, reason)
        self._finish(run.task_id, "Aborted", reason, run.keep)

    def _loop(self, run: _Run) -> None:
        while run.idx < len(run.steps):
            run.resume.wait()
            if run.cancel.is_set():
                return self._abort_run(run, "Aborted by user")

            step = run.steps[run.idx]
            params = dict(step["parameters"])
            if run.confirmed:
                params.update(confirmed=True, pending=run.pending)
                run.confirmed = False
            if run.choice is not None:
                params["choice"] = run.choice
                run.choice = None

            db.set_subtask(step["id"], "Running")
            result = self.agents[step["agent"]].execute(step["action"], params, run.context)
            if run.cancel.is_set():
                return self._abort_run(run, "Aborted by user")

            if result.needs_confirmation:
                run.pending = result.output
                if self._auto_approved(step["action"]):
                    db.log(run.task_id, f"auto-approved by policy: {step['action']}", step["id"])
                    run.confirmed = True
                    continue
                run.awaiting = {
                    "message": result.message,
                    "choices": result.output.get("choices", 0),
                    "options": result.output.get("options", []),
                }
                run.decision.clear()
                db.set_subtask(step["id"], "Pending", result.message)
                db.log(run.task_id, f"awaiting confirmation: {step['action']}", step["id"])
                with self._lock:
                    self._transition(run.task_id, "Awaiting Confirmation")
                run.decision.wait()
                run.awaiting = None
                if not run.approved or run.cancel.is_set():
                    db.log(run.task_id, "confirmation rejected", step["id"])
                    return self._abort_run(run, "Rejected by user")
                db.log(run.task_id, "confirmation granted", step["id"])
                with self._lock:
                    self._transition(run.task_id, "Executing")
                run.confirmed = True
                continue

            db.set_subtask(step["id"], "Completed" if result.ok else "Failed", result.message)
            status = "ok" if result.ok else "failed"
            db.log(run.task_id, f"{step['agent']}.{step['action']} {status}: {result.message[:200]}", step["id"])
            if not result.ok:
                if self._should_auto_fix(run, step, result):
                    run.fix_attempted = True
                    run.context["last_error"] = result.message
                    self._append_fix_steps(run)
                    run.idx += 1
                    continue
                return self._finish(run.task_id, "Failed",
                                    f"Step {run.idx + 1} ({step['action']}) failed: {result.message}", run.keep)
            run.context.update(result.output)
            run.last_message = result.message
            run.idx += 1

        self._finish(run.task_id, "Completed", None, run.keep)
        if settings.get()["voice_output"] and run.last_message:
            voice.speak(run.last_message[:300])  # FR-35
