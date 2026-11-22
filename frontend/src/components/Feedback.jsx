import { TERMINAL } from "../format";

// Shown as soon as FLOW has planned a request: the steps it will take.
export function Understood({ task }) {
  const steps = task.subtasks || [];
  return (
    <section className="card understood">
      <p className="eyebrow">I understood</p>
      <h3>{task.command}</h3>
      {steps.length ? (
        <ol className="steps">
          {steps.map((s) => (
            <li key={s.subtask_id} className="step pending">
              <span className="step-icon"><span className="todo-mark">○</span></span>
              <div className="step-body">
                <strong>{s.agent}</strong>
                <span className="muted"> · {s.action.replace(/_/g, " ")}</span>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="muted">Starting…</p>
      )}
    </section>
  );
}

// Shown when a request has finished, with what happened.
export function Outcome({ task, onClose }) {
  const ok = task.outcome === "Completed";
  const last = [...(task.subtasks || [])].reverse().find((s) => s.result)?.result || "";
  return (
    <section className="card outcome-card">
      <p className="eyebrow">{ok ? "Done" : "Not completed"}</p>
      <h3>{task.command}</h3>
      <p className={ok ? "ok-text" : "bad-text"}>{ok ? last || "Finished." : task.error || last}</p>
      <button className="btn ghost" onClick={onClose}>Dismiss</button>
    </section>
  );
}

export function isWorking(task) {
  return !!task && !TERMINAL.includes(task.status);
}
