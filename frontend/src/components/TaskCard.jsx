import { api } from "../api";
import { tone } from "../format";

// The task that is running right now: progress, every step, and the controls.
export default function TaskCard({ task, onError }) {
  const steps = task.subtasks || [];
  const done = steps.filter((s) => s.status === "Completed").length;
  const percent = steps.length ? Math.round((done / steps.length) * 100) : 0;
  const act = (fn) => fn(task.task_id).catch((e) => onError(e.message || String(e)));
  const canPause = task.status === "Executing";
  const canResume = task.status === "Paused";
  const canStop = ["Executing", "Paused", "Awaiting Confirmation"].includes(task.status);

  return (
    <section className="card task-card">
      <header className="task-head">
        <div>
          <p className="eyebrow">Running now</p>
          <h3>{task.command}</h3>
        </div>
        <span className={`badge ${tone(task.status)}`}>{task.status}</span>
      </header>

      <div className="progress" aria-label={`${percent}% complete`}>
        <span style={{ width: `${percent}%` }} />
      </div>
      <p className="muted small">{done} of {steps.length} steps done</p>

      <ol className="steps">
        {steps.map((s) => (
          <li key={s.subtask_id} className={`step ${s.status.toLowerCase()}`}>
            <span className="step-icon">{stepIcon(s.status)}</span>
            <div className="step-body">
              <strong>{s.agent}</strong>
              <span className="muted"> · {s.action.replace(/_/g, " ")}</span>
              {s.result && <div className="result">{s.result}</div>}
            </div>
          </li>
        ))}
      </ol>

      <div className="task-actions">
        <button className="btn ghost" disabled={!canPause} onClick={() => act(api.pause)}>Pause</button>
        <button className="btn ghost" disabled={!canResume} onClick={() => act(api.resume)}>Resume</button>
        <button className="btn danger" disabled={!canStop} onClick={() => act(api.abort)}>Stop</button>
      </div>
    </section>
  );
}

function stepIcon(status) {
  if (status === "Completed") return <span className="ok-mark">✓</span>;
  if (status === "Failed") return <span className="bad-mark">✕</span>;
  if (status === "Running") return <span className="spinner" />;
  return <span className="todo-mark">○</span>;
}
