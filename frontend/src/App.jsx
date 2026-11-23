import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { useLive } from "./useLive";
import { briefly, speak } from "./speech";
import { TERMINAL } from "./format";
import Sidebar from "./components/Sidebar";
import Toasts, { useToasts } from "./components/Toasts";
import Approval from "./components/Approval";
import Assistant from "./views/Assistant";
import History from "./views/History";
import Settings from "./views/Settings";
import Help from "./views/Help";

export default function App() {
  const live = useLive();
  const [view, setView] = useState("assistant");
  const [online, setOnline] = useState(false);
  const [status, setStatus] = useState(null);
  const [recent, setRecent] = useState([]);
  const [latest, setLatest] = useState(null);     // the request the user just made, followed to the end
  const { toasts, push, dismiss } = useToasts();
  const settingsRef = useRef(null);
  const announced = useRef(new Set());            // tasks already reported, so each is spoken once
  const awaitingSpoken = useRef("");
  const fail = useCallback((message) => push(message, "error"), [push]);

  // Backend health: shown in the sidebar.
  useEffect(() => {
    const check = () => api.status().then((s) => { setStatus(s); setOnline(true); }).catch(() => setOnline(false));
    check();
    const timer = setInterval(check, 8000);
    return () => clearInterval(timer);
  }, []);

  // Settings are read again when the page changes, so saved changes apply at once.
  useEffect(() => {
    api.settings().then((s) => { settingsRef.current = s; }).catch(() => {});
  }, [view]);

  const refreshRecent = useCallback(() => {
    api.tasks("", 1).then(setRecent).catch(() => {});
  }, []);
  useEffect(() => { refreshRecent(); }, [refreshRecent]);

  // Report a finished task: a notification, a spoken result, and an updated list.
  const announce = useCallback((task) => {
    if (announced.current.has(task.task_id)) return;
    announced.current.add(task.task_id);
    const last = [...(task.subtasks || [])].reverse().find((s) => s.result)?.result || "";
    const ok = task.outcome === "Completed";
    push(`${ok ? "Done" : "Not completed"} · ${task.command}`, ok ? "ok" : "error");
    const text = ok
      ? `Done. ${briefly(last) || "Your request is complete."}`
      : `Sorry, that did not work. ${briefly(task.error || last)}`;
    if (settingsRef.current?.voice_output) speak(text, settingsRef.current.voice_volume);
    refreshRecent();
  }, [push, refreshRecent]);

  // Follow the latest request until it finishes, so nothing is missed even for very short tasks.
  useEffect(() => {
    if (!latest) return undefined;
    if (TERMINAL.includes(latest.status)) {
      announce(latest);
      return undefined;
    }
    const timer = setInterval(() => {
      api.task(latest.task_id).then(setLatest).catch(() => {});
    }, 700);
    return () => clearInterval(timer);
  }, [latest?.task_id, latest?.status, announce]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmitted = useCallback((task) => {
    setLatest(task);
    refreshRecent();
  }, [refreshRecent]);

  const active = live.active;
  const awaiting = active && active.status === "Awaiting Confirmation" ? live.awaiting : null;
  const busy = !!active || (!!latest && !TERMINAL.includes(latest.status));

  // Ask for approval out loud, once per request.
  useEffect(() => {
    if (!awaiting || !settingsRef.current?.voice_output) return;
    const key = `${active.task_id}:awaiting`;
    if (awaitingSpoken.current === key) return;
    awaitingSpoken.current = key;
    speak("I need your approval before I continue.", settingsRef.current.voice_volume);
  }, [awaiting, active?.task_id]); // eslint-disable-line react-hooks/exhaustive-deps

  const decide = (approved, choice) => {
    api.confirm(active.task_id, approved, choice).catch((e) => fail(e.message));
  };

  return (
    <div className="shell">
      <Sidebar
        view={view}
        setView={setView}
        online={online}
        model={status?.ollama?.model}
        ollamaError={status?.ollama?.error}
      />
      <main className="content">
        {view === "assistant" && (
          <Assistant
            active={active}
            latest={latest}
            busy={busy}
            recent={recent}
            onError={fail}
            onSubmitted={handleSubmitted}
            onDismiss={() => setLatest(null)}
          />
        )}
        {view === "history" && <History onError={fail} />}
        {view === "settings" && <Settings onError={fail} onSaved={(m) => push(m, "ok")} />}
        {view === "help" && <Help />}
      </main>
      {awaiting && <Approval awaiting={awaiting} onDecide={decide} />}
      <Toasts toasts={toasts} dismiss={dismiss} />
    </div>
  );
}
