# FLOW

FLOW is a voice- and text-driven assistant for Windows. Tell it what you want in plain words, such as "open gmail", "make a calculator and run it" or "increase the volume". FLOW works out the steps, does them on your computer or in your browser, and tells you the result out loud.

It asks for your approval before it deletes, overwrites, moves, installs or runs anything. You can pause, resume or stop a task at any time.

Your speech and language are processed on your computer. The only internet access is to the websites FLOW opens.

Software Engineering project, Practical Group G2, NED University of Engineering and Technology.
Authors: Rumaisah (CS-24063) and Umaima (CS-24055).

---

## Features

- **Voice and text input.** Click the microphone (or press Ctrl+Space) and speak. FLOW sends your words when you pause. You can also type.
- **Planning.** Common requests are handled by fixed rules. Harder requests go to a local AI model (Ollama). Every step is checked against a list of allowed actions before it runs.
- **Programs and files.** Open programs by name, open files and folders, and create, copy, move, read and delete files inside your allowed folders.
- **Browser.** Open websites in Chrome, search the web, type into web pages (for example, a question in ChatGPT), compose Gmail drafts (never sent automatically), and play the best YouTube match.
- **Coding.** Create a project, open it in VS Code, write the code, install the packages it needs (after approval), run it, and try one automatic fix if it fails.
- **Control.** Pause, resume or stop a task. Stop any task from any window with Ctrl+Shift+Esc.
- **Safety.** Deletes, overwrites, moves, installs, program runs and shell commands need your approval. The approval box shows exactly what will happen.
- **Results.** Each result is shown on screen and spoken aloud. A history of your requests is kept, with search, delete and export.
- **Settings.** Choose the AI model, search engine, approval policy, voice output and more.

## How a request works

1. You speak or type a request.
2. The **planner** turns it into steps, using rules or the AI model.
3. The **orchestrator** runs the steps in order and pauses for approval when needed.
4. Each step is done by an **agent**: system, coding, web or assistant.
5. The window shows what FLOW understood, each step as it runs, and the final result.

## Project structure

```
FLOW/
├── README.md
├── .gitignore
├── backend/                     Python program that does the work
│   ├── main.py                  starts the server on 127.0.0.1:8765
│   ├── server.py                HTTP and live-update endpoints
│   ├── orchestrator.py          runs steps, approvals, pause, stop, auto-fix
│   ├── planner.py               turns a request into steps
│   ├── state.py                 task stages and allowed changes between them
│   ├── db.py                    database: requests, steps, log, settings
│   ├── settings.py              saved preferences, checked before saving
│   ├── config.py                basic settings (model, folders, limits)
│   ├── llm.py                   talks to Ollama
│   ├── voice.py                 speech to text and text to speech
│   ├── desktop.py               keys, typing, windows, volume, play key
│   ├── agents/
│   │   ├── base.py              shared rules and result format; opens Chrome
│   │   ├── system_agent.py      programs, files, folders, keys, volume, shell
│   │   ├── coding_agent.py      projects, code, running, packages, Git
│   │   ├── web_agent.py         websites, search, typing, YouTube playback
│   │   └── assistant_agent.py   answers questions
│   ├── tests/test_core.py       53 automated tests
│   ├── pytest.ini
│   └── requirements.txt         Python packages
├── frontend/                    the desktop window (Electron + React)
│   ├── electron/
│   │   ├── main.js              opens the window, starts the backend
│   │   └── preload.js
│   ├── src/
│   │   ├── App.jsx              layout, follows each request, announces results
│   │   ├── api.js               every call to the backend
│   │   ├── useLive.js           live connection to the backend
│   │   ├── audio.js             microphone recording
│   │   ├── speech.js            spoken results
│   │   ├── format.js            labels, colours and times
│   │   ├── styles.css           the look of the app
│   │   ├── main.jsx
│   │   ├── components/          command box, task card, approval, and more
│   │   └── views/               Assistant, History, Settings, Help
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── package-lock.json
└── submission/                  course documents (SRS, design, reports)
```

## Requirements

- Windows 10 or 11 (64-bit)
- Python 3.10 or newer
- Node.js 18 or newer
- Ollama (https://ollama.com)
- Google Chrome (for browsing; FLOW uses the default browser if Chrome is not found)
- VS Code and Git (optional, for opening projects and version control)
- A microphone (optional, for voice)

## Setup

Open PowerShell and run the steps below once.

**1. Get the AI model**

```powershell
ollama pull qwen2.5:3b
```

This is the default model for FLOW. It is about 1.9 GB.

**2. Set up the backend**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks the activation script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**3. Set up the frontend**

Open a second PowerShell window:

```powershell
cd frontend
npm install
```

If the Electron download stops partway, use the mirror and try again:

```powershell
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
npm install
```

## Running FLOW

Use three PowerShell windows.

**Window 1: the backend**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:FLOW_OLLAMA_MODEL = "qwen2.5:3b"
python main.py
```

Wait for `Application startup complete`, and leave this window open.

**Window 2: the frontend dev server**

```powershell
cd frontend
npm run dev
```

Wait for `Local: http://localhost:5173/`, and leave this window open.

**Window 3: the desktop window**

```powershell
cd frontend
$env:FLOW_PYTHON = "<full path to backend\.venv\Scripts\python.exe>"
npm run electron
```

Replace `<full path to ...>` with the real path, for example `C:\Users\YourName\Desktop\FLOW\backend\.venv\Scripts\python.exe`.

## Choosing the AI model

- The default is `qwen2.5:3b` (smaller, faster, lighter on memory).
- For better planning of complex requests, you can use the larger `qwen2.5-coder:7b`. It needs more memory and runs more slowly.
- Set the model with `$env:FLOW_OLLAMA_MODEL` before starting the backend, or in **Settings → Language model**. A value saved in Settings overrides the environment variable.

## Speech recognition

- The default speech model is `medium.en`, which is the most accurate. The first use downloads about 1.5 GB, so you need internet access and free disk space.
- On a slower computer, use the smaller model:

```powershell
$env:FLOW_WHISPER_MODEL = "small.en"
python main.py
```

## Running the tests

The tests check FLOW's logic without opening real programs, websites or microphones.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:FLOW_MOCK = "1"
python -m pytest -v
```

A successful run ends with `53 passed`. `FLOW_MOCK` only lasts for the current PowerShell window.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Click the mic, or hold Ctrl+Space | Start talking. Pause to send. |
| Ctrl+Shift+Esc | Stop the running task, from any window |

## Where your data is stored

- **History and settings:** `backend\flow.db`, in the backend folder.
- **New projects and files:** your Desktop, unless you change the projects folder in Settings.

The database file is excluded from Git, so your personal history is not uploaded.

## Limitations

- Windows only.
- FLOW controls the keyboard, windows and files. It does not click arbitrary buttons on the screen.
- Planning quality depends on the AI model that is installed.
- Speech accuracy depends on your microphone and the room.
- Pause takes effect between steps, not in the middle of one.
- The "wake word" setting is stored but not yet implemented.

## Course documents

The `submission/` folder contains the documents for the course: the requirements specification (SRS), the design and database description, the sprint backlog and review, the wireframes, the solution report, and the presentation outline.

## Troubleshooting

| Problem | What to do |
|---|---|
| "FLOW's backend is not running" | Start `python main.py` in the backend window. |
| "Model ... is not installed" | Run `ollama pull qwen2.5:3b`, then restart the backend. |
| Electron says it failed to install | Use the mirror command in Setup step 3, then run `npm install` again. |
| Voice says it isn't installed | Run `python -m pip install -r requirements.txt` in the backend environment. |
| Microphone does nothing | Check the Windows microphone permission and the default input device. |