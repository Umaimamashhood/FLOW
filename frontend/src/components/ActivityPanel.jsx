// Chronological list of commands and results, with the live log of the running task.
export default function ActivityPanel({ recent, active }) {
  const when = (iso) => (iso ? new Date(iso).toLocaleTimeString() : "");
  return (
    <section className="panel">
      <h2>Activity</h2>
      {active && (
        <div className="log">
          {active.log.slice(-20).map((entry, i) => (
            <div key={i} className="log-line">
              <span className="time">{when(entry.timestamp)}</span> {entry.event}
            </div>
          ))}
        </div>
      )}
      <ul className="activity">
        {recent.map((t) => (
          <li key={t.task_id}>
            <span className="time">{when(t.created_at)}</span>
            <span className="cmd">{t.command}</span>
            <span className={`outcome ${t.outcome || "running"}`}>{t.outcome || t.status}</span>
            {t.error && <div className="result">{t.error}</div>}
          </li>
        ))}
        {recent.length === 0 && !active && <li className="muted">Nothing yet. Try “open VS Code” or “play a song”.</li>}
      </ul>
    </section>
  );
}
