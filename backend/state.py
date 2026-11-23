"""Task lifecycle state machine (SRS 3.3.1)."""

TASK_STATES = frozenset({
    "Idle", "Listening", "Planning", "Awaiting Confirmation",
    "Executing", "Paused", "Completed", "Failed",
})
TERMINAL = frozenset({"Completed", "Failed"})

_VALID = {
    "Idle": {"Listening", "Planning"},
    "Listening": {"Planning"},
    "Planning": {"Executing"},
    "Executing": {"Awaiting Confirmation", "Paused", "Completed"},
    "Awaiting Confirmation": {"Executing"},
    "Paused": {"Executing"},
}


class InvalidTransition(Exception):
    pass


def check_transition(current: str | None, new: str) -> None:
    """Raise InvalidTransition unless current -> new is permitted."""
    if current not in TASK_STATES or new not in TASK_STATES:
        raise InvalidTransition(f"unknown state: {current!r} -> {new!r}")
    if new == "Failed":  # any non-terminal state may fail (error or abort)
        if current in TERMINAL:
            raise InvalidTransition(f"cannot fail a task that is {current}")
        return
    if new not in _VALID.get(current, set()):
        raise InvalidTransition(f"{current} -> {new} is not allowed")
