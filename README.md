# FLOW

A voice- and text-driven multi-agent coding assistant for Windows. FLOW takes a request such as
"open VS Code, create a Python file called scraper, write a web scraper and save it", plans the steps,
dispatches them to the System, Coding and Web agents, and reports back. All language processing runs
locally through Ollama. Nothing leaves the machine by default.

Software Engineering project, Practical Group G2, NED University. Specification: SRS v1.0.

## Structure

    flow-project/
      backend/      Python 3.10+ FastAPI service, agents, SQLite, tests
      frontend/     Electron shell + React (Vite) interface
      docs/         Voice command cheat sheet, SRS traceability
      README.md

## Quick start (development)

1. Install Ollama from https://ollama.com and pull a model:

       ollama pull qwen2.5-coder:7b

2. Backend:

       cd backend
       python -m venv .venv
       .venv\Scripts\activate            (Windows; on macOS/Linux use: source .venv/bin/activate)
       pip install -r requirements.txt
       pip install -r requirements-optional.txt   (voice and keyboard control; optional)
       python -m flow                     (serves http://127.0.0.1:8765)

3. Frontend:

       cd frontend
       npm install
       npm run dev                        (Vite dev server on :5173, in one terminal)
       npm run electron                   (in a second terminal; it starts the backend too)

   Set `FLOW_PYTHON` if your interpreter is not called `python`.

Without Ollama or the optional packages, FLOW still runs in a degraded mode: the rule-based planner handles
common commands, and the interface shows a banner explaining what is unavailable.

## Tests

    cd backend
    FLOW_MOCK=1 pytest

Mock mode replaces the LLM, speech, and desktop control with stubs and never opens real applications
or browser tabs. The suite covers the state machine, path safety, confirmations, pause/resume/abort,
the automatic fix, media best-match selection, git, history and settings, the REST API, and the WebSocket.

## Build a Windows installer

    cd backend
    pip install pyinstaller -r requirements.txt -r requirements-optional.txt
    pyinstaller --onefile --name flow-backend --collect-submodules flow flow/__main__.py
    cd ../frontend
    npm run dist                       (produces frontend/release/FLOW Setup x.exe)

The packaged app starts `flow-backend.exe` from its resources folder. This pipeline has not yet been
run on a Windows machine; see docs/TRACEABILITY.md for the verification status.

## Keyboard

| Shortcut | Action |
|---|---|
| Hold Ctrl+Space | Push to talk |
| Ctrl+Shift+Esc | Abort the running task (works when FLOW is not focused) |

## Privacy

Speech recognition uses faster-whisper, and text-to-speech uses pyttsx3. Both run locally. The backend
binds only to 127.0.0.1. Audio is never written to disk. Telemetry is not included. The only outbound
connections are the Web Agent's browser requests, which open in the user's own browser, and the optional
video-result lookup.

See docs/CHEATSHEET.md for example commands and docs/TRACEABILITY.md for how each SRS requirement is covered.
