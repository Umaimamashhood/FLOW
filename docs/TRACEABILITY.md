# SRS traceability and verification status

Status key: **Done** means implemented and covered by an automated test. **Partial** means implemented
with a documented limitation. **Not built** means not in this version. "Manual" means it needs a real
Windows machine, a microphone, Ollama, or a desktop session, so it is not covered by the automated suite.

## Voice and text input (FR-1 to FR-5)

| ID | Status | Notes |
|---|---|---|
| FR-1 | Partial | faster-whisper on the device. Needs the model download and a microphone (manual). |
| FR-2 | Done | Command bar. |
| FR-3 | Partial | Push-to-talk (hold Ctrl+Space or the mic button) works. Wake word not built. |
| FR-4 | Done | Transcripts below the confidence threshold go to the input box for review. |
| FR-5 | Done | Global Ctrl+Shift+Esc aborts (manual check). |

## Planning (FR-6 to FR-10)

| ID | Status | Notes |
|---|---|---|
| FR-6 | Partial | Single or multi-step is implicit in the plan; no explicit classification field. |
| FR-7 | Done | Each sub-task has one agent. |
| FR-8 | Done | Outputs such as `project_path` and `main_file` flow to later steps. |
| FR-9 | Not built | Ambiguous requests are rejected, not clarified. |
| FR-10 | Done | Unsupported requests are rejected, with the supported capabilities listed. |

## System Agent (FR-11 to FR-16)

| ID | Status | Notes |
|---|---|---|
| FR-11 | Done | Alias map and PATH lookup. |
| FR-12, FR-13 | Done | Create, list, delete, move; rename is covered by move. Permitted folders only. |
| FR-14 | Partial | Keyboard shortcuts via PyAutoGUI, with focus checks. No mouse control. |
| FR-15 | Done | Delete, move, and overwrite need confirmation, subject to the policy. |
| FR-16 | Not built | System information. |

## Coding Agent (FR-17 to FR-25)

| ID | Status | Notes |
|---|---|---|
| FR-17, FR-18, FR-19 | Done | Generation through Ollama; mock templates otherwise. Opens in VS Code if installed. |
| FR-20 | Not built | Editing an existing file with diff approval. |
| FR-21 | Done | Confirmation, output capture, 30 s limit, and a cancellable run. |
| FR-22 | Done | One automatic fix attempt, then the task fails with the errors shown. |
| FR-23 | Done | Tkinter, pygame, and Qt programs launch in their own window. |
| FR-24 | Done | Python syntax check before saving. |
| FR-25 | Done | git init and commit (requires Git). |

## Web Agent (FR-26 to FR-31)

| ID | Status | Notes |
|---|---|---|
| FR-26, FR-27 | Done | Browser opens; search engine is selectable. |
| FR-28 | Partial | Reads the results page and opens the best title match. The page format can change, which breaks parsing; the code then falls back to opening the results. |
| FR-29 | Done | Ambiguous results are listed and the user picks one. |
| FR-30 | Partial | Pause and resume both send the media play/pause key; next works. Browser automation is not used. |
| FR-31 | Not built | Page summarisation. |

## Orchestration, voice output, persistence, models (FR-32 to FR-42)

| ID | Status | Notes |
|---|---|---|
| FR-32 | Done | Stops at the first unrecoverable failure and names the step. |
| FR-33, FR-34 | Done | Live timeline over WebSocket; pause, resume, abort. Pause takes effect between sub-tasks. |
| FR-35 | Partial | Spoken summary via pyttsx3 (manual check). |
| FR-36 | Partial | Setting in the UI. No hotkey. |
| FR-37 | Partial | Tasks and sub-tasks are saved with state changes. With history off, the task is deleted when it finishes, so it is briefly in the database. |
| FR-38 | Done | Newest first, 50 per page, case-insensitive search. |
| FR-39 | Done | Stored in the preferences table, validated on save. |
| FR-40 | Done | Delete one entry; clear all after confirmation. |
| FR-41, FR-42 | Done | Model list and selection; clear banners for Ollama errors. |

## Behaviour and use cases (Section 3.3)

The state machine matches the valid transitions in SRS 3.3.1, and invalid transitions are rejected in
code and tested. Startup marks interrupted tasks as failed (SRS 4.3.1). Confirmation policy: Always Confirm
is the default; Confirm Destructive Only and Unattended apply only to file operations (S-11). Program runs
always ask (S-15).

## Non-functional requirements

| ID | Status | Notes |
|---|---|---|
| P-1 to P-10 | Manual | Targets are stated but have not been benchmarked on the recommended hardware. |
| S-11 to S-15 | Done | Confirmations, fail-safe, focus checks, and source review before runs. |
| S-16 | Done | Binds to 127.0.0.1. |
| S-17 | Partial | Paths outside permitted folders are rejected rather than confirmed. |
| S-18 | Partial | No elevation is requested. Not verified on Windows. |
| S-19 | Done | Action log with timestamp, sub-task and outcome. |
| S-20 | Done | Audio is held in memory and never written to disk. |
| S-21 | Not built | No credentials are stored, so DPAPI is not needed yet. |
| S-22 | Done | Path, name, and key validation; length limits. |
| 4.3.1 Reliability | Done | Three LLM retries with a 2 s delay; interrupted-task recovery. |
| 4.3.4 Modularity | Partial | One module per agent with a common interface. Prompts are still in code, not in template files. |
| 4.3.5 Extensibility | Partial | Agents are registered in code, not from a configuration file. |
| 4.3.7 Testability | Done | Mock mode and 29 automated tests. |
| 4.3.8 Privacy | Done | No telemetry; local models. |
| Ch. 5 Migrations | Done | Versioned migrations in the schema_version table. |
| Ch. 5 Export | Done | JSON export from Settings and GET /export. |

## Verification status

- Backend: 29 automated tests pass in mock mode on Linux. The REST API and WebSocket were exercised.
- Frontend: the production build succeeds (Vite). It has not been run inside Electron.
- Not yet verified: the Electron window on Windows, real speech recognition and synthesis, PyAutoGUI,
  the PyInstaller and installer build, and the performance targets.
