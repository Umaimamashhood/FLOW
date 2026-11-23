# FLOW

A voice- and text-driven assistant for Windows. Give it a request such as "open gmail", "make a calculator and run it", or "increase the volume", and it plans the steps, runs them, and reports back. The local AI model (through Ollama) chooses the steps. Your data stays on your computer, except for the websites FLOW opens in your browser.

## Structure

```
flow-project/
├── README.md
├── docs/
│   ├── CHEATSHEET.md          example commands and troubleshooting
│   └── TRACEABILITY.md        SRS requirement status
├── backend/                   Python code (run with: python main.py)
│   ├── main.py                starts the server on 127.0.0.1:8765
│   ├── server.py              HTTP and WebSocket endpoints
│   ├── orchestrator.py        runs the steps, confirmations, pause and abort
│   ├── planner.py             turns a request into steps
│   ├── agents/                System, Coding, Web and Assistant actions
│   ├── db.py, settings.py, state.py, config.py, llm.py
│   ├── voice.py, desktop.py   speech, keyboard, windows and media keys
│   ├── requirements.txt       the one requirements file
│   ├── pytest.ini
│   └── tests/test_core.py
└── frontend/                  Electron desktop window (React)
    ├── electron/main.js       starts the backend and the window
    ├── src/                   the React interface
    └── package.json
```

## Setup

1. Install Ollama from https://ollama.com and download a model:

       ollama pull qwen2.5-coder:7b

2. Backend, in a PowerShell window:

       cd backend
       python -m venv .venv
       .\.venv\Scripts\Activate.ps1
       python -m pip install -r requirements.txt

3. Frontend, in a second PowerShell window:

       cd frontend
       npm install

## Run

1. Window 1 (leave it running):

       cd frontend
       npm run dev

2. Window 2:

       cd frontend
       $env:FLOW_PYTHON = "<full path to backend\.venv\Scripts\python.exe>"
       npm run electron

Without Ollama, FLOW still runs for simple requests. The window shows a banner explaining what is unavailable.

## Tests

    cd backend
    $env:FLOW_MOCK = "1"
    python -m pytest -q

Mock mode replaces the model, speech, and desktop control with stubs, so tests never open real programs or browsers.

## Build a Windows installer (advanced)

    cd backend
    python -m pip install pyinstaller
    pyinstaller --onefile --name flow-backend --collect-submodules agents main.py
    cd ../frontend
    npm run dist

This has not been run on a Windows machine yet.

## Keyboard

| Shortcut | Action |
|---|---|
| Hold Ctrl+Space | Push to talk |
| Ctrl+Shift+Esc | Abort the running task (works from any window) |

## Privacy

Speech recognition and text-to-speech run on your computer. The backend listens only on 127.0.0.1. Audio is not stored. There is no telemetry.

See docs/CHEATSHEET.md for example commands.
