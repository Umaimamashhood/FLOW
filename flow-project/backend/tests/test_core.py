import shutil
import time

import pytest

from flow import config, db, desktop, planner, settings, state
from flow.agents import web_agent
from flow.agents.base import Result
from flow.agents.coding_agent import CodingAgent, is_gui_program
from flow.agents.system_agent import SystemAgent, safe_path
from flow.agents.web_agent import WATCH, WebAgent
from flow.orchestrator import ConflictError, Orchestrator


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", True)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(config, "ALLOWED_DIRS", [tmp_path])
    db.init_db()
    return tmp_path


def wait_until(predicate, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("condition not reached in time")


def wait_status(task_id, statuses, timeout=10.0):
    wait_until(lambda: db.get_task(task_id)["status"] in statuses, timeout)
    return db.get_task(task_id)


def use_plan(monkeypatch, steps):
    monkeypatch.setattr(planner, "plan", lambda cmd: [dict(s, parameters=dict(s["parameters"])) for s in steps])


def step(agent, action, **params):
    return {"agent": agent, "action": action, "parameters": params}


# ---------- state machine, paths, planner ----------

def test_invalid_transition_rejected():
    with pytest.raises(state.InvalidTransition):
        state.check_transition("Idle", "Completed")


def test_failing_an_executing_task_is_allowed():
    state.check_transition("Executing", "Failed")


def test_path_outside_permitted_folders_rejected(tmp_path):
    with pytest.raises(PermissionError):
        safe_path(str(tmp_path.parent / "outside.txt"))


def test_path_inside_permitted_folder_allowed(tmp_path):
    assert safe_path(str(tmp_path / "a.txt")) == (tmp_path / "a.txt").resolve()


def test_rule_planner_make_calculator():
    steps = planner.plan("make a calculator")
    assert [s["action"] for s in steps] == ["create_folder", "open_in_vscode", "build_project", "run_program"]


def test_rule_planner_spec_example_partially_and_file_creation():
    steps = planner.plan("open vs code, create a python file called scraper, write a web scraper and save it")
    assert [s["action"] for s in steps] == ["open_app", "create_file", "write_code"]
    assert steps[1]["parameters"]["path"] == "scraper.py"


def test_unsupported_request_rejected():
    with pytest.raises(planner.Unsupported):
        planner.plan("dance the tango")


def test_planner_strips_confirmed_flag():
    steps = planner._validate({"steps": [
        {"agent": "System", "action": "delete", "parameters": {"path": "x", "confirmed": True}}]})
    assert "confirmed" not in steps[0]["parameters"]


def test_planner_rejects_unknown_action():
    assert planner._validate({"steps": [{"agent": "System", "action": "format_disk", "parameters": {}}]}) is None


# ---------- agents ----------

def test_delete_requires_confirmation(sandbox):
    target = sandbox / "keep.txt"
    target.write_text("data")
    agent = SystemAgent()
    r = agent.execute("delete", {"path": str(target)}, {})
    assert r.needs_confirmation and target.exists()
    r = agent.execute("delete", {"path": str(target), "confirmed": True}, {})
    assert r.ok and not target.exists()


def test_gui_detection():
    assert is_gui_program("import tkinter as tk\n")
    assert not is_gui_program("print('hi')\n")


def test_hotkey_parsing():
    assert desktop.parse_hotkey("Ctrl+S") == ["ctrl", "s"]
    with pytest.raises(ValueError):
        desktop.parse_hotkey("ctrl+rm")


def test_send_keys_refused_without_focus_backend(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)

    def no_backends():
        raise ImportError("missing")

    monkeypatch.setattr(desktop, "_load_backends", no_backends)
    ok, _ = desktop.send_hotkey("Notepad", ["ctrl", "s"])
    assert not ok


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_git_init_creates_repository(sandbox):
    folder = config.PROJECTS_DIR / "repo"
    folder.mkdir(parents=True)
    (folder / "main.py").write_text("print(1)\n")
    r = CodingAgent().execute("git_init", {}, {"project_path": str(folder)})
    assert r.ok and (folder / ".git").exists()


def test_media_plays_clear_best_match(monkeypatch):
    from flow import media_queue
    media_queue.pop_all()
    monkeypatch.setattr(web_agent, "search_candidates", lambda q: [
        ("aaaaaaaaaaa", "Cooking pasta at home"), ("bbbbbbbbbbb", "Shape of You - Ed Sheeran")])
    r = WebAgent().execute("play_media", {"query": "shape of you"}, {})
    assert r.ok and media_queue.pop_all() == [WATCH.format("bbbbbbbbbbb")]


def test_ambiguous_media_asks_then_plays_chosen_result(sandbox, monkeypatch):
    opened = []
    monkeypatch.setattr(web_agent, "open_url", opened.append)
    monkeypatch.setattr(web_agent, "search_candidates", lambda q: [
        ("aaaaaaaaaaa", "Cooking pasta"), ("bbbbbbbbbbb", "Driving tutorial")])
    use_plan(monkeypatch, [step("Web", "play_media", query="shape of you")])
    orch = Orchestrator()
    tid = orch.submit("play shape of you")
    task = wait_status(tid, {"Awaiting Confirmation"})
    assert orch.awaiting_info()["choices"] == 2
    orch.confirm(tid, True, choice=1)
    wait_status(tid, {"Completed"})
    from flow import media_queue
    assert media_queue.pop_all() == [WATCH.format("bbbbbbbbbbb")]


# ---------- orchestration ----------

def test_make_calculator_end_to_end():
    orch = Orchestrator()
    task_id = orch.submit("make a calculator")
    wait_status(task_id, {"Awaiting Confirmation"})  # running the program needs approval
    orch.confirm(task_id, True)
    wait_status(task_id, {"Completed"})
    assert "tkinter" in (config.PROJECTS_DIR / "calculator" / "main.py").read_text()


def test_destructive_task_waits_for_confirmation(sandbox, monkeypatch):
    target = sandbox / "old.txt"
    target.write_text("x")
    use_plan(monkeypatch, [step("System", "delete", path=str(target))])
    orch = Orchestrator()
    task_id = orch.submit("delete the old file")
    wait_status(task_id, {"Awaiting Confirmation"})
    assert target.exists()
    orch.confirm(task_id, True)
    wait_status(task_id, {"Completed"})
    assert not target.exists()


def test_rejected_confirmation_aborts(sandbox, monkeypatch):
    target = sandbox / "keep.txt"
    target.write_text("x")
    use_plan(monkeypatch, [step("System", "delete", path=str(target))])
    orch = Orchestrator()
    task_id = orch.submit("delete it")
    wait_status(task_id, {"Awaiting Confirmation"})
    orch.confirm(task_id, False)
    task = wait_status(task_id, {"Failed"})
    assert task["outcome"] == "Aborted" and target.exists()


def test_unattended_policy_skips_file_confirmation(sandbox, monkeypatch):
    settings.update({"confirmation_policy": "Unattended"})
    target = sandbox / "gone.txt"
    target.write_text("x")
    use_plan(monkeypatch, [step("System", "delete", path=str(target))])
    task_id = Orchestrator().submit("delete it")
    assert wait_status(task_id, {"Completed"})["status"] == "Completed"
    assert not target.exists()


def test_pause_and_resume(monkeypatch):
    def slow(self, params, ctx):
        time.sleep(0.4)
        return Result(True, "listed")

    monkeypatch.setattr(SystemAgent, "do_list_dir", slow)
    use_plan(monkeypatch, [step("System", "list_dir"), step("System", "list_dir")])
    orch = Orchestrator()
    tid = orch.submit("list twice")
    orch.pause(tid)
    assert db.get_task(tid)["status"] == "Paused"
    time.sleep(0.6)
    assert db.get_task(tid)["status"] == "Paused"
    orch.resume(tid)
    wait_status(tid, {"Completed"})


def test_abort_stops_remaining_steps(monkeypatch):
    def slow(self, params, ctx):
        time.sleep(0.3)
        return Result(True, "listed")

    monkeypatch.setattr(SystemAgent, "do_list_dir", slow)
    use_plan(monkeypatch, [step("System", "list_dir")] * 3)
    orch = Orchestrator()
    tid = orch.submit("list three times")
    orch.abort(tid)
    task = wait_status(tid, {"Failed"})
    assert task["outcome"] == "Aborted"
    assert task["subtasks"][-1]["result"] == "Not run"


def test_pause_is_rejected_when_no_task_runs():
    with pytest.raises(ConflictError):
        Orchestrator().pause(999)


def test_auto_fix_recovers_from_failing_program(sandbox, monkeypatch):
    use_plan(monkeypatch, [
        step("System", "create_folder", name="demo"),
        step("System", "create_file", path="main.py", content="raise SystemExit(3)\n"),
        step("Coding", "run_program"),
    ])
    orch = Orchestrator()
    tid = orch.submit("make a demo program")
    wait_status(tid, {"Awaiting Confirmation"})
    orch.confirm(tid, True)  # first run fails; the fix and the re-run need confirmation again
    wait_until(lambda: len(db.get_task(tid)["subtasks"]) == 5 and
               db.get_task(tid)["status"] == "Awaiting Confirmation")
    orch.confirm(tid, True)
    task = wait_status(tid, {"Completed"})
    assert [s["action"] for s in task["subtasks"]] == [
        "create_folder", "create_file", "run_program", "fix_program", "run_program"]
    assert "mock project" in (config.PROJECTS_DIR / "demo" / "main.py").read_text()


def test_auto_fix_gives_up_after_one_attempt(sandbox, monkeypatch):
    monkeypatch.setattr(CodingAgent, "_fix", lambda self, *a: "raise SystemExit(5)\n")
    use_plan(monkeypatch, [
        step("System", "create_folder", name="broken"),
        step("System", "create_file", path="main.py", content="raise SystemExit(3)\n"),
        step("Coding", "run_program"),
    ])
    orch = Orchestrator()
    tid = orch.submit("make a broken program")
    wait_status(tid, {"Awaiting Confirmation"})
    orch.confirm(tid, True)
    wait_until(lambda: len(db.get_task(tid)["subtasks"]) == 5 and
               db.get_task(tid)["status"] == "Awaiting Confirmation")
    orch.confirm(tid, True)
    task = wait_status(tid, {"Failed"})
    assert task["outcome"] == "Failed" and "failed" in task["error"]


def test_history_off_leaves_no_record(monkeypatch):
    settings.update({"history_enabled": False})
    tid = Orchestrator().submit("search for python")
    wait_until(lambda: db.get_task(tid) is None)


def test_settings_validation_and_persistence():
    with pytest.raises(ValueError):
        settings.update({"confirmation_policy": "Anything"})
    with pytest.raises(ValueError):
        settings.update({"nope": 1})
    with pytest.raises(ValueError):
        settings.update({"history_enabled": "yes"})
    settings.update({"history_enabled": False, "confirmation_policy": "Unattended"})
    s = settings.get()
    assert s["history_enabled"] is False and s["confirmation_policy"] == "Unattended"


def test_api_end_to_end(sandbox):
    from fastapi.testclient import TestClient
    from flow.server import app

    with TestClient(app) as client:
        r = client.post("/commands", json={"text": "search for python"})
        assert r.status_code == 200
        tid = r.json()["task_id"]
        wait_until(lambda: client.get(f"/tasks/{tid}").json()["status"] == "Completed")
        assert any(t["task_id"] == tid for t in client.get("/tasks").json())
        assert client.get("/status").json()["mock"] is True
        assert "confirmation_policy" in client.get("/settings").json()
        assert client.get("/export").json()["tasks"]
        assert client.post(f"/tasks/{tid}/pause").status_code == 409


def test_websocket_pushes_task_snapshot(sandbox, monkeypatch):
    from fastapi.testclient import TestClient
    from flow.server import app

    def slow(self, params, ctx):  # keep the task visible long enough for the 0.4 s poll to see it
        time.sleep(1.5)
        return Result(True, "listed")

    monkeypatch.setattr(SystemAgent, "do_list_dir", slow)
    use_plan(monkeypatch, [step("System", "list_dir")])
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            first = ws.receive_json()
            assert first["active"] is None and first["awaiting"] is None
            client.post("/commands", json={"text": "list things"})
            seen_task = False
            for _ in range(20):
                snap = ws.receive_json()
                if snap["active"] and snap["active"]["command"] == "list things":
                    seen_task = True
                    break
            assert seen_task


# ---------- general-purpose tools and the model planner ----------
import io
import struct
import wave

from flow import planner as planner_mod
from flow import voice
from flow.agents import system_agent as sa_mod
from flow.agents.assistant_agent import AssistantAgent


def _silent_wav():
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<4h", 0, 16384, -16384, 0))
    return buf.getvalue()


def test_voice_wav_decodes_without_audio_library():
    samples = voice.wav_to_samples(_silent_wav())
    assert len(samples) == 4 and abs(samples[1] - 0.5) < 1e-3


def test_transcribe_reports_missing_speech_package(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)
    monkeypatch.setattr(voice, "available", lambda: False)
    with pytest.raises(voice.VoiceUnavailable):
        voice.transcribe(_silent_wav())


def test_llm_plan_is_used_when_model_answers(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)
    monkeypatch.setattr(planner_mod.llm, "generate", lambda *a, **k: (
        '{"steps":[{"agent":"Web","action":"open_url","parameters":{"url":"https://mail.google.com","confirmed":true}}]}'))
    steps = planner_mod.plan("open gmail")
    assert steps == [{"agent": "Web", "action": "open_url", "parameters": {"url": "https://mail.google.com"}}]


def test_model_failure_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)

    def down(*a, **k):
        raise ConnectionError("down")

    monkeypatch.setattr(planner_mod.llm, "generate", down)
    actions = [s["action"] for s in planner_mod.plan("make a calculator")]
    assert actions == ["create_folder", "open_in_vscode", "build_project", "run_program"]


def test_invalid_model_plan_is_rejected(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)
    monkeypatch.setattr(planner_mod.llm, "generate", lambda *a, **k: '{"steps":[{"agent":"System","action":"format_disk"}]}')
    actions = [s["action"] for s in planner_mod.plan("make a calculator")]  # falls back to the rules
    assert actions[0] == "create_folder"


def test_run_shell_asks_before_running(sandbox):
    r = SystemAgent().execute("run_shell", {"command": "Get-ChildItem"}, {})
    assert r.needs_confirmation and "Get-ChildItem" in r.message


def test_copy_and_read_inside_permitted_folder(sandbox):
    src = sandbox / "a.txt"
    src.write_text("hi")
    assert SystemAgent().execute("copy", {"src": str(src), "dst": str(sandbox / "b.txt")}, {}).ok
    assert (sandbox / "b.txt").read_text() == "hi"
    r = SystemAgent().execute("read_file", {"path": str(sandbox / "b.txt")}, {})
    assert r.ok and r.message == "hi"


def test_start_menu_shortcut_matching(tmp_path, monkeypatch):
    root = tmp_path / "Programs"
    (root / "Accessories").mkdir(parents=True)
    (root / "Accessories" / "File Explorer.lnk").write_text("x")
    (root / "Accessories" / "Notepad.lnk").write_text("x")
    monkeypatch.setattr(sa_mod, "start_menu_roots", lambda: [root])
    assert sa_mod.find_start_menu_shortcut("file explorer").name == "File Explorer.lnk"
    assert sa_mod.find_start_menu_shortcut("nothing here") is None


def test_open_app_does_not_launch_in_mock_mode():
    r = SystemAgent().execute("open_app", {"name": "file explorer"}, {})
    assert r.ok and "mock" in r.message


def test_assistant_answers_in_mock_mode():
    r = AssistantAgent().execute("answer", {"text": "hello"}, {})
    assert r.ok and "mock" in r.message


def test_missing_packages_are_detected(tmp_path):
    from flow.agents.coding_agent import missing_packages
    source = "import os\nimport flow_no_such_package_xyz\nfrom tkinter import Tk\n"
    assert missing_packages(source, tmp_path) == ["flow_no_such_package_xyz"]


def test_auto_run_skips_confirmation_inside_projects_folder(sandbox):
    settings.update({"auto_run_programs": True})
    folder = config.PROJECTS_DIR / "hello"
    folder.mkdir(parents=True)
    main = folder / "main.py"
    main.write_text("print('hi from flow')\n")
    r = CodingAgent().execute("run_program", {}, {"main_file": str(main)})
    assert r.ok and "hi from flow" in r.message


def test_voice_volume_accepts_whole_numbers():
    s = settings.update({"voice_volume": 1})
    assert s["voice_volume"] == 1.0 and isinstance(s["voice_volume"], float)


def test_clear_requests_never_reach_the_model(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)

    def must_not_call(*a, **k):
        raise AssertionError("the model should not be asked for a clear request")

    monkeypatch.setattr(planner_mod.llm, "generate", must_not_call)
    assert planner_mod.plan("make a calculator")[0]["action"] == "create_folder"
    assert planner_mod.plan("search for python")[0]["action"] == "search"


def test_unclear_requests_go_to_the_model(monkeypatch):
    monkeypatch.setattr(config, "MOCK_MODE", False)
    monkeypatch.setattr(planner_mod.llm, "generate", lambda *a, **k: (
        '{"steps":[{"agent":"Assistant","action":"answer","parameters":{"text":"hi"}}]}'))
    assert planner_mod.plan("make a website for my bakery")[0]["action"] == "answer"
