# Testing Document

**Project:** FLOW (backend and desktop interface)
**Group:** Practical Group G2

## 1. Testing approach

Testing covers three levels:

1. **Automated tests** (`backend/tests/test_core.py`). These run with `FLOW_MOCK=1`, which replaces the language model, speech engine, browser and keyboard with stubs. They check logic, rules and the API. They do not open real programs or websites.
2. **Partition tests.** Inputs are grouped into classes (valid, invalid, boundary) and one case from each class is tested. These are included in the automated suite and listed in section 4.
3. **Manual acceptance tests.** These check the features that need a real Windows machine, a microphone, Chrome and Ollama. They are listed in section 5, with blank result columns to be completed during the demonstration.

## 2. Environment

- Windows 11, Python 3.12, Node.js 24, Electron 31.7.7
- Ollama with qwen2.5-coder:7b
- Automated run: `cd backend`, then `$env:FLOW_MOCK = "1"`, then `python -m pytest -q`

## 3. Automated test results

**Result: 50 passed, 0 failed (run time about 4 seconds).**

### 3.1 Requirement-based test cases

| Test ID | Requirement | Test (function in test_core.py) | Expected result | Result |
|---|---|---|---|---|
| T-01 | 3.3.1 state machine | test_invalid_transition_rejected | Invalid transition raises an error | Pass |
| T-02 | 3.3.1 state machine | test_failing_an_executing_task_is_allowed | Executing task can move to Failed | Pass |
| T-03 | FR-7, FR-8 | test_rule_planner_make_calculator | Steps are created in order for each agent | Pass |
| T-04 | FR-6, FR-7 | test_rule_planner_spec_example_partially_and_file_creation | Compound request split into steps | Pass |
| T-05 | FR-10 | test_unsupported_request_rejected | Unsupported request is rejected | Pass |
| T-06 | S-11 | test_planner_strips_confirmed_flag | Model cannot approve its own actions | Pass |
| T-07 | FR-15, S-11 | test_planner_rejects_unknown_action | Actions not in the catalogue are rejected | Pass |
| T-08 | FR-15 | test_delete_requires_confirmation | Delete does nothing until confirmed | Pass |
| T-09 | FR-23 | test_gui_detection | Graphical programs are detected | Pass |
| T-10 | FR-14, S-13 | test_hotkey_parsing | Valid key combinations accepted, unsafe ones rejected | Pass |
| T-11 | FR-14, S-13 | test_send_keys_refused_without_focus_backend | Keys are not sent when the target window cannot be confirmed | Pass |
| T-12 | FR-25 | test_git_init_creates_repository | Git repository is created | Pass |
| T-13 | FR-28 | test_media_plays_clear_best_match | Clear title match opens the best video | Pass |
| T-14 | FR-29 | test_ambiguous_media_asks_then_plays_chosen_result | Unclear match asks, then plays the user's choice | Pass |
| T-15 | FR-17, FR-18, FR-19 | test_make_calculator_end_to_end | Project folder and calculator code created; run waits for approval | Pass |
| T-16 | FR-15, S-11 | test_destructive_task_waits_for_confirmation | Task pauses until the user confirms the delete | Pass |
| T-17 | FR-15 | test_rejected_confirmation_aborts | Rejected action is aborted and the file is kept | Pass |
| T-18 | S-11 (Unattended policy) | test_unattended_policy_skips_file_confirmation | File operation runs without prompt only when the user opted in | Pass |
| T-19 | FR-32, FR-33, FR-34 | test_pause_and_resume | Task pauses and resumes between steps | Pass |
| T-20 | FR-34 | test_abort_stops_remaining_steps | Abort stops the remaining steps | Pass |
| T-21 | FR-34 | test_pause_is_rejected_when_no_task_runs | Pausing with no running task returns a conflict | Pass |
| T-22 | FR-22 | test_auto_fix_recovers_from_failing_program | Failed program gets one fix, then runs | Pass |
| T-23 | FR-22 | test_auto_fix_gives_up_after_one_attempt | After the second failure the task fails and shows the errors | Pass |
| T-24 | FR-37 | test_history_off_leaves_no_record | No task remains after completion when history is off | Pass |
| T-25 | FR-39 | test_settings_validation_and_persistence | Invalid settings are rejected; valid ones are saved | Pass |
| T-26 | FR-38, FR-41 | test_api_end_to_end | Command, history, status, settings and export endpoints respond | Pass |
| T-27 | FR-33 | test_websocket_pushes_task_snapshot | Live task updates are pushed to the window | Pass |
| T-28 | FR-1 | test_voice_wav_decodes_without_audio_library | Recorded audio is decoded correctly | Pass |
| T-29 | FR-1, FR-42 | test_transcribe_reports_missing_speech_package | Clear message when the speech package is missing | Pass |
| T-30 | FR-6 | test_llm_plan_is_used_when_model_answers | Model plan is used when valid | Pass |
| T-31 | FR-42 | test_model_failure_falls_back_to_rules | Rules are used when the model is unavailable | Pass |
| T-32 | FR-7 | test_invalid_model_plan_is_rejected | Invalid model plan is rejected and rules are used | Pass |
| T-33 | FR-6 | test_clear_requests_never_reach_the_model | Common requests are handled without the model | Pass |
| T-34 | FR-6 | test_unclear_requests_go_to_the_model | Unclear requests are sent to the model | Pass |
| T-35 | FR-12, FR-13 | test_path_inside_permitted_folder_allowed | Path inside permitted folder accepted | Pass |
| T-36 | FR-12, S-17 | test_path_outside_permitted_folders_rejected | Path outside permitted folders rejected | Pass |
| T-37 | FR-13 | test_copy_and_read_inside_permitted_folder | Files copied and read within permitted folders | Pass |
| T-38 | FR-11 | test_start_menu_shortcut_matching | Program found by its Start menu name | Pass |
| T-39 | FR-11 | test_open_app_does_not_launch_in_mock_mode | Launch is simulated in mock mode | Pass |
| T-40 | FR-26, FR-27 | test_open_url_uses_chrome_in_mock_mode | Website opens in Chrome | Pass |
| T-41 | FR-27 | test_type_on_page_mock_ok | Text is typed into a page | Pass |
| T-42 | FR-16 | test_run_shell_asks_before_running | Shell command requires approval | Pass |
| T-43 | FR-15 (install) | test_install_dependencies_asks_first | Package install requires approval | Pass |
| T-44 | FR-21 | test_missing_packages_are_detected | Missing third-party packages found from imports | Pass |
| T-45 | FR-21 | test_detect_packages_skips_stdlib_and_local_files | Standard library and local files are ignored | Pass |
| T-46 | FR-21, FR-22 | test_missing_package_is_installed_then_program_runs | Missing package is installed, then the program runs | Pass |
| T-47 | FR-21 | test_auto_run_skips_confirmation_inside_projects_folder | Program runs without approval only when the user enabled auto-run inside the projects folder | Pass |
| T-48 | FR-35 | test_voice_volume_accepts_whole_numbers | Voice volume setting accepts whole numbers | Pass |
| T-49 | FR-35 | test_set_volume_mock_ok | Volume action succeeds in mock mode | Pass |
| T-50 | FR-42 (answers) | test_assistant_answers_in_mock_mode | Questions are answered in text | Pass |

### 3.2 Requirements without an automated test

These are checked manually (section 5) or not yet checked:

- FR-3 (push-to-talk): manual test M-01.
- FR-4 (low-confidence speech review): not implemented in this version, because speech is sent automatically.
- FR-9 (clarifying questions): not implemented.
- FR-16 (system information): not implemented.
- FR-20 (diff approval for edits): not implemented.
- FR-24 (syntax check before saving): implemented, tested indirectly through build tests, no direct test.
- FR-30 (playback control): manual test M-05.
- FR-31 (page summary): not implemented.
- FR-36 (voice output hotkey): not implemented.
- FR-40 (delete history entry, clear all): manual test M-10.
- S-16 (localhost only): manual test M-11.
- S-19 (audit log): log entries are written; no automated check.
- Chapter 5 migrations and JSON export: export is tested through the API test; migrations are not tested.

## 4. Partition testing

| Input | Partition | Example | Expected behaviour | Covered by |
|---|---|---|---|---|
| Request type | Clear, common phrase | "make a calculator" | Handled by rules, no model call | T-33 |
| Request type | Unclear phrase | "make a website for my bakery" | Sent to model | T-34 |
| Request type | Unsupported, no model | "dance the tango" | Rejected with a message | T-05 |
| Model answer | Valid JSON, known actions | `{"steps":[…]}` | Used as the plan | T-30 |
| Model answer | Unknown action | `format_disk` | Rejected, rules used | T-07, T-32 |
| Path | Inside permitted folder | Desktop file | Allowed | T-35 |
| Path | Outside permitted folder | `C:\Windows` | Rejected | T-36 |
| Key combination | Valid | `ctrl+s` | Accepted | T-10 |
| Key combination | Unsafe or unknown | `ctrl+rm` | Rejected | T-10 |
| Policy | Always Confirm | Delete request | Waits for approval | T-16 |
| Policy | Unattended | Delete request | Runs without prompt | T-18 |
| Media match | Clear | "shape of you" with matching title | Opens best match | T-13 |
| Media match | Unclear | Titles don't match | Asks user to choose | T-14 |
| Program run | Command-line program | Prints text | Output captured | T-15 |
| Program run | Graphical program | Imports tkinter | Opens its own window | T-09 |
| Program run | Failure | Exit code 3 | One fix attempt, then rerun | T-22, T-23 |
| Speech input | Audio of 16-bit mono 16 kHz | Silent WAV | Decoded | T-28 |

## 5. Manual acceptance tests

Run these on the demonstration machine. Record the result in the last column.

| Test ID | Feature | Steps | Expected result | Result |
|---|---|---|---|---|
| M-01 | Voice input | Hold the mic for about 2 seconds, say "open gmail", release | Text appears as "Heard: …", Gmail opens in Chrome | Not yet run |
| M-02 | Voice accuracy | Say 5 short commands | At least 4 of 5 transcribed correctly | Not yet run |
| M-03 | YouTube playback | Type "play shape of you" | Video opens in Chrome and starts within 10 seconds | Not yet run |
| M-04 | Gmail compose | Type "compose an email to sam@example.com saying hi" | Draft opens with address and text, not sent | Not yet run |
| M-05 | Playback control | Type "pause", then "resume" | Video pauses, then resumes | Not yet run |
| M-06 | ChatGPT typing | Type "open chatgpt and ask it to explain recursion" | Question appears in the chat box | Not yet run |
| M-07 | Volume | Type "increase the volume" | System volume rises | Not yet run |
| M-08 | Program build and run | Type "make a calculator and run it", approve prompts | Folder created, VS Code opens, calculator window opens | Not yet run |
| M-09 | Package install | Type "make a car game with pygame and run it", approve install and run | Pygame installed, game window opens | Not yet run |
| M-10 | History | Open History, search, delete one entry, clear all | Each action works and clear asks first | Not yet run |
| M-11 | Localhost only | Run `netstat -ano \| findstr 8765` | Backend listens on 127.0.0.1 only | Not yet run |
| M-12 | Abort | Start a multi-step task, press Ctrl+Shift+Esc | Task stops within 1 second | Not yet run |
| M-13 | Confirmation | Type "delete a file on my Desktop" (test file), choose Cancel | File is kept | Not yet run |
| M-14 | Error messages | Stop Ollama, submit a command | Banner explains Ollama is not running | Not yet run |

## 6. Defects found and fixed during development

| # | Defect | Cause | Fix | Verification |
|---|---|---|---|---|
| D-01 | "make a calculator" opened Windows Calculator | Model read the request as "open an app" | Rules run first for clear requests | T-33 |
| D-02 | Calculator template failed to load | Escaped quotes in source file | Corrected string quoting | T-15 |
| D-03 | Calculator rejected `2*(3)` | Parentheses were not allowed | Allowed in calculator input | Fixed. Not separately verified |
| D-04 | Duplicate run step | Rules added two run steps | Duplicate removed | T-15 |
| D-05 | Voice returned an error | Speech package not installed | Clear message; install step documented | T-29 |
| D-06 | Voice failed on a version mismatch | Audio library and speech library versions did not match | Audio decoded directly | T-28 |
| D-07 | Browser showed "Failed to fetch" | Error responses lacked CORS headers | Errors returned in a readable form | Fixed. Manual check M-14 not yet run |
| D-08 | Recording could not be decoded | Compressed recording in browser | Raw 16 kHz recording used | Fixed. Manual check M-01 not yet run |
| D-09 | Video opened but did not play | Results page layout changed, search failed | Search through yt-dlp, play key sent | Fixed. Manual check M-03 not yet run |
| D-10 | Server ignored new code | Old process still running on port 8765 | Old process stopped and the app restarted | Fixed. Not covered by a test |
| D-11 | Test hung | Task finished before the live update was sent | Test made the task visible longer | T-27 |

## 7. Known gaps and risks

- Manual tests (section 5) have not been run yet.
- No automated tests run on real Windows, real Chrome or real speech.
- Performance targets (P-1 to P-9) have not been measured on the recommended hardware.
- Planning quality depends on the installed language model.
- The traceability document (docs/TRACEABILITY.md) predates recent changes and needs updating.
