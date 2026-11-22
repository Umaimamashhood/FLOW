---
title: "Solution"
subtitle: "FLOW: a voice- and text-driven multi-agent assistant for Windows"
---

**Group:** G2 (Rumaisah CS-24063, Umaima CS-24055)

**GitHub repository:** [insert repository link]

**The developed system.** FLOW accepts a voice or typed request, such as "open gmail" or "make a calculator and run it". It turns the request into ordered steps, runs each step through a specialised agent on the user's computer, and reports the result. Its main features are:

- **Voice and text input.** Speech is converted to text on the computer and sent when the button is released.
- **Planning.** Clear requests use fixed rules. Unclear requests go to a local language model, whose plan is checked against a list of allowed actions.
- **Desktop control.** FLOW opens installed programs, manages files and folders, types text, presses shortcuts, brings windows forward, and changes the system volume.
- **Browser control.** FLOW opens sites in Chrome, searches, types into pages such as ChatGPT, prepares Gmail drafts (never sent automatically), and plays the best YouTube match.
- **Programming.** FLOW creates a project, opens it in VS Code, writes the code, installs the packages it imports, runs it, and attempts one automatic fix if the run fails.
- **Control and safety.** Deletions, overwrites, installs and program runs need approval. Tasks can be paused, resumed or aborted (Ctrl+Shift+Esc works from any window).

**How it addresses the problem.** Everyday tasks span several programs and many clicks, and developers repeat the same project setup each time. Existing assistants such as Windows Voice Access and Siri mostly run single commands, and many use the cloud. FLOW runs several steps from one request, keeps processing local, and handles project setup and program runs.

**Technologies and tools.** The backend uses Python, FastAPI, SQLite, and Ollama with the qwen2.5-coder 7B model. Speech recognition uses faster-whisper and speech output uses pyttsx3. Desktop control uses PyAutoGUI and PyGetWindow, and YouTube search uses yt-dlp. The desktop window uses Electron, React and Vite. Automated tests use pytest. Version control uses Git and GitHub.

**Improvements over existing approaches.** FLOW runs several steps from one request, keeps speech and language processing on the user's computer, automates developer tasks from project creation to a running program, and asks for approval before any change that cannot be undone.

**Limitations.** FLOW controls the keyboard, windows and files. It does not click arbitrary buttons or read the screen. Planning quality depends on the installed model, speech accuracy depends on the microphone, and the system runs on Windows only.
