import { api } from "../api";

const STATUS_TONE = { Pending: "pending", Running: "running", Completed: "done", Failed: "failed" };

export default function TaskTimeline({ task, onError }) {
  if (!task) {
    return (
      <section className="panel">
        <h2>Task timeline</h2>
        <p className="muted">No task is running. Give FLOW a command to start.</p>
      </section>
    );
  }
  const run = (fn) => fn(task.task_id).catch(onError);
  const canPause = task.status === "Executing";
  const canResume = task.status === "Paused";
  const canAbort = ["Executing", "Paused", "Awaiting Confirmation"].includes(task.status);

  return (
    <section className="panel">
      <h2>Task timeline</h2>
      <p className="muted">{task.command}</p>
      <ol className="timeline">
        {task.subtasks.map((s) => (
          <li key={s.subtask_id} className={STATUS_TONE[s.status] || ""}>
            <span className="pill">{s.status}</span>
            <strong>{s.agent}</strong> · {s.action.replace(/_/g, " ")}
            {s.result && <div className="result">{s.result}</div>}
          </li>
        ))}
      </ol>
      <div className="controls">
        <button className="secondary" disabled={!canPause} onClick={() => run(api.pause)}>Pause</button>
        <button className="secondary" disabled={!canResume} onClick={() => run(api.resume)}>Resume</button>
        <button className="danger" disabled={!canAbort} onClick={() => run(api.abort)}>Abort</button>
      </div>
      <p className="muted small">Shortcut: Ctrl+Shift+Esc aborts from anywhere.</p>
    </section>
  );
}
