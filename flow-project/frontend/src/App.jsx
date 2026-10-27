import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { useLive } from "./useLive";
import CommandBar from "./components/CommandBar";
import ActivityPanel from "./components/ActivityPanel";
import TaskDetail from "./components/TaskDetail";
import TaskTimeline from "./components/TaskTimeline";
import StatusIndicator from "./components/StatusIndicator";
import ConfirmationDialog from "./components/ConfirmationDialog";
import HistoryView from "./components/HistoryView";
import SettingsView from "./components/SettingsView";
import HelpView from "./components/HelpView";
import ErrorBanner from "./components/ErrorBanner";

const VIEWS = [
  ["assistant", "Assistant"],
  ["history", "History"],
  ["settings", "Settings"],
  ["help", "Help"],
];

export default function App() {
  const live = useLive();
  const [view, setView] = useState("assistant");
  const [error, setError] = useState("");
  const [status, setStatus] = useState(null);
  const [listening, setListening] = useState(false);
  const [recent, setRecent] = useState([]);
  const [draft, setDraft] = useState("");
  const [openTask, setOpenTask] = useState(null);

  const reportError = useCallback((err) => setError(err?.message || String(err)), []);

  const loadStatus = useCallback(() => api.status().then(setStatus).catch(reportError), [reportError]);
  useEffect(() => {
    loadStatus();
    const timer = setInterval(loadStatus, 10000);
    return () => clearInterval(timer);
  }, [loadStatus]);

  // Refresh the activity list whenever a task starts, changes status or finishes.
  const activeKey = `${live.active?.task_id ?? "none"}:${live.active?.status ?? ""}`;
  useEffect(() => {
    api.tasks("", 1).then(setRecent).catch(() => {});
  }, [activeKey]);

  const active = live.active;
  const awaiting = active && active.status === "Awaiting Confirmation" ? live.awaiting : null;
  const ollamaWarning = status && !status.mock && status.ollama.error ? status.ollama.error : "";

  const decide = (approved, choice) => {
    api.confirm(active.task_id, approved, choice).catch(reportError);
  };

  return (
    <div className="app">
      <header>
        <h1>FLOW</h1>
        <nav>
          {VIEWS.map(([key, label]) => (
            <button key={key} className={view === key ? "active" : "secondary"} onClick={() => setView(key)}>
              {label}
            </button>
          ))}
        </nav>
        <StatusIndicator listening={listening} active={active} awaiting={awaiting} />
      </header>

      <ErrorBanner message={!live.connected ? "Reconnecting to the FLOW backend…" : ""} tone="warning" />
      <ErrorBanner message={ollamaWarning} tone="warning" />
      <ErrorBanner message={error} onDismiss={() => setError("")} />

      {view === "assistant" && (
        <main className="grid">
          <section>
            <CommandBar
              disabled={!!active}
              draft={draft}
              setDraft={setDraft}
              listening={listening}
              setListening={setListening}
              onError={reportError}
            />
            {openTask
              ? <TaskDetail taskId={openTask} onBack={() => setOpenTask(null)} onError={reportError} />
              : <ActivityPanel recent={recent} active={active} onSelect={setOpenTask} />}
          </section>
          <aside>
            <TaskTimeline task={active} onError={reportError} />
          </aside>
        </main>
      )}
      {view === "history" && <HistoryView onBack={() => setView("assistant")} onError={reportError} />}
      {view === "settings" && <SettingsView onBack={() => setView("assistant")} onError={reportError} />}
      {view === "help" && <HelpView onBack={() => setView("assistant")} />}

      {awaiting && <ConfirmationDialog awaiting={awaiting} onDecide={decide} />}
    </div>
  );
}
