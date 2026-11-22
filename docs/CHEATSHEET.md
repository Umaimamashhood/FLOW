# FLOW command cheat sheet

Type a command in the box and press Enter, or hold the mic button (or Ctrl+Space) and speak. Speech is sent when you release.

| What you want | Example |
|---|---|
| Open a program | open vs code, open chrome, open file explorer |
| Open a website in Chrome | open gmail, open classroom |
| Search the web | search for rust borrow checker |
| Type into a page | open chatgpt and ask it to explain recursion |
| Compose an email (not sent) | compose an email to sam@example.com saying hi |
| Play a song or video | play shape of you |
| Playback | pause, resume, next |
| Volume | increase the volume, decrease the volume, mute |
| Build a program | make a calculator, make a car game with pygame and run it |
| Write code into a file | create a python file called scraper, write a web scraper and save it |
| Run a program | run it |
| Files | copy notes.txt to backup.txt, delete old.txt |
| Keys | press ctrl s in notepad, type hello in notepad |
| Questions | what is 12 times 7 |

## Confirmations

FLOW asks before it deletes, moves, overwrites, installs packages, runs a program, or runs a shell command. Settings let you change this policy.

## Keyboard

- **Ctrl+Space** (hold): push to talk
- **Ctrl+Shift+Esc**: abort the running task from anywhere

## Troubleshooting

- *Cannot reach the backend*: start it with `python main.py` in the backend folder.
- *Ollama is not running*: start the Ollama app, then try again.
- *Speech does not work*: run `python -m pip install -r requirements.txt` in the backend environment.
- *Playback does not start*: check that `pyautogui` and `pygetwindow` are installed (`python -m pip show pyautogui`).
