# FLOW voice command cheat sheet

Say a command while holding **Ctrl+Space** (or the mic button), or type it in the command bar.

| Area | Examples |
|---|---|
| Applications | "open VS Code", "open chrome", "launch notepad" |
| Projects | "make a calculator", "make a javascript clock" |
| Files | "create a python file called scraper", "create a text file called notes" |
| Git | "init git" and "commit" (inside the current project) |
| Media | "play shape of you", "pause", "resume", "next" |
| Web | "search for rust borrow checker", "open https://example.com" |
| Keys | "press ctrl s in notepad" (the window must be focused) |

## Confirmations

FLOW always asks before it deletes, moves, overwrites a file, or runs a program. You can relax this
in Settings:

- **Always Confirm** (default): ask for every action that changes files or runs code.
- **Confirm Destructive Only**: overwrites go through without asking.
- **Unattended**: delete, move, and create also go through. Program runs always ask.

## Keyboard

- **Ctrl+Space** (hold): push to talk
- **Ctrl+Shift+Esc**: abort the running task from anywhere

## Troubleshooting

- *Cannot reach the backend*: start it with `python -m flow` in the backend folder.
- *Ollama is not running*: start the Ollama app, then try again.
- *Model not installed*: run `ollama pull <model>`, then pick it in Settings.
- *Microphone not working*: check the Windows microphone privacy setting and the default input device.
