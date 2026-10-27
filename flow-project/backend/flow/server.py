"""FastAPI backend, bound to 127.0.0.1 only (S-16)."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import Body, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from flow import config, db, llm, media_queue, settings, state, voice
from flow.orchestrator import ConflictError, Orchestrator

orchestrator = Orchestrator()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    settings.apply_runtime()
    yield


app = FastAPI(title="FLOW backend", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(file://.*|null|https?://(localhost|127\.0\.0\.1)(:\d+)?)$",
    allow_methods=["*"],
    allow_headers=["*"],
)


class CommandIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    mode: Literal["text", "voice"] = "text"


class ConfirmIn(BaseModel):
    approved: bool
    choice: int | None = Field(default=None, ge=0, le=9)


class SpeakIn(BaseModel):
    text: str = Field(max_length=2000)


def _call(fn, *args, **kwargs):
    """Map domain errors to HTTP status codes."""
    try:
        return fn(*args, **kwargs)
    except (ConflictError, state.InvalidTransition) as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # HTTPException keeps CORS headers, so the browser can show this message
        raise HTTPException(500, f"Something went wrong: {exc}") from exc


def _snapshot() -> dict:
    tid = orchestrator.active_task_id
    return {"active": db.get_task(tid) if tid else None, "awaiting": orchestrator.awaiting_info(),
            "media": orchestrator.last_media()}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict:
    return {
        "mock": config.MOCK_MODE,
        "ollama": llm.status(),
        "active_task_id": orchestrator.active_task_id,
        "awaiting": orchestrator.awaiting_info(),
        "voice_available": voice.available(),
        "schema_version": db.schema_version(),
    }


@app.get("/models")
def models() -> dict:
    try:
        return {"models": llm.list_models()}
    except Exception as exc:
        raise HTTPException(503, "Ollama is not running. Start it and try again.") from exc


@app.get("/settings")
def get_settings() -> dict:
    return settings.get()


@app.put("/settings")
def put_settings(values: dict[str, Any] = Body(...)) -> dict:
    return _call(settings.update, values)


@app.post("/commands")
def submit_command(cmd: CommandIn) -> dict:
    task_id = _call(orchestrator.submit, cmd.text.strip(), cmd.mode)
    return db.get_task(task_id) or {"task_id": task_id, "status": "Executing", "history": False}


@app.post("/abort")
def abort_active() -> dict:
    _call(orchestrator.abort)
    return {"aborted": True}


@app.get("/tasks")
def list_tasks(search: str = "", page: int = Query(1, ge=1)) -> list[dict]:
    return db.list_tasks(search=search, page=page)


@app.get("/tasks/{task_id}")
def get_task(task_id: int) -> dict:
    task = db.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


@app.post("/tasks/{task_id}/pause")
def pause_task(task_id: int) -> dict:
    _call(orchestrator.pause, task_id)
    return db.get_task(task_id) or {}


@app.post("/tasks/{task_id}/resume")
def resume_task(task_id: int) -> dict:
    _call(orchestrator.resume, task_id)
    return db.get_task(task_id) or {}


@app.post("/tasks/{task_id}/abort")
def abort_task(task_id: int) -> dict:
    _call(orchestrator.abort, task_id)
    return {"aborted": task_id}


@app.post("/tasks/{task_id}/confirm")
def confirm_task(task_id: int, body: ConfirmIn) -> dict:
    _call(orchestrator.confirm, task_id, body.approved, body.choice)
    return {"accepted": True}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int) -> dict:
    if task_id == orchestrator.active_task_id:
        raise HTTPException(409, "Stop the running task before deleting it.")
    if not db.delete_task(task_id):
        raise HTTPException(404, "Task not found")
    return {"deleted": task_id}


@app.post("/history/clear")
def clear_history() -> dict:
    if orchestrator.active_task_id is not None:
        raise HTTPException(409, "Stop the running task before clearing history.")
    db.clear_history()
    return {"cleared": True}


@app.get("/export")
def export() -> JSONResponse:
    return JSONResponse(db.export_all(), headers={"Content-Disposition": 'attachment; filename="flow-export.json"'})


@app.post("/voice/transcribe")
async def transcribe(request: Request) -> dict:
    audio = await request.body()
    if not audio or len(audio) > 20 * 1024 * 1024:
        raise HTTPException(400, "No usable audio was received")
    try:
        result = await asyncio.to_thread(voice.transcribe, audio)
    except voice.VoiceUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Speech recognition failed: {exc}") from exc
    result["needs_review"] = result["confidence"] < settings.get()["asr_confidence_min"]  # FR-4
    return result


@app.get("/media/pending")
def pending_media() -> dict:
    """Links the desktop player window should open."""
    return {"urls": media_queue.pop_all()}


@app.post("/voice/speak")
def speak(body: SpeakIn) -> dict:
    return {"spoken": voice.speak(body.text)}


@app.websocket("/ws")
async def live(socket: WebSocket) -> None:
    """Pushes the active task and any pending confirmation whenever they change (SRS 3.1.4)."""
    await socket.accept()
    last = None
    try:
        while True:
            snap = await asyncio.to_thread(_snapshot)
            if snap != last:
                await socket.send_json(snap)
                last = snap
            await asyncio.sleep(0.4)
    except (WebSocketDisconnect, RuntimeError):
        return
