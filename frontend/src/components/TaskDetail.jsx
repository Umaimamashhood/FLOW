import { useEffect, useState } from "react";
import { api } from "../api";

// Everything FLOW did for one task: each step with its parameters and exact result, plus the log.
export default function TaskDetail({ taskId, onBack, onError }) {
  const [task, setTask] = useState(null);

  useEffect(() => {
    setTask(null);
    api.task(taskId).then(setTask).catch(onError);
  }, [taskId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!task) {
    return (
      <section className="panel">
        <div className="toolbar"><button className="secondary" onClick={onBack}>Back</button></div>
        <p className="muted">Loading…</p>
      </section>
    );
  }

  const outcome = task.outcome || task.status;
  return (
    <section className="panel">
      <div className="toolbar"><button className="secondary" onClick={onBack}>Back</button></div>
      <h2>{task.command}</h2>
      <p className="muted">
        <span className={`outcome ${task.outcome || "running"}`}>{outcome}</span>
        {" · "}{new Date(task.created_at).toLocaleString()}
      </p>
      {task.error && <p className="banner error">{task.error}</p>}

      <h3>Steps</h3>
      <ol className="timeline">
        {task.subtasks.map((s) => (
          <li key={s.subtask_id} className={s.status === "Completed" ? "done" : s.status === "Failed" ? "failed" : ""}>
            <span className="pill">{s.status}</span>
            <strong>{s.agent}</strong> · {s.action.replace(/_/g, " ")}
            <div className="params">{JSON.stringify(s.parameters)}</div>
            {s.result && <pre className="message">{s.result}</pre>}
          </li>
        ))}
      </ol>

      <h3>Log</h3>
      <div className="log">
        {task.log.map((entry, i) => (
          <div key={i} className="log-line">
            <span className="time">{new Date(entry.timestamp).toLocaleTimeString()}</span> {entry.event}
          </div>
        ))}
      </div>
    </section>
  );
}
