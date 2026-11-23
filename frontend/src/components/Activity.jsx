import { tone, when } from "../format";

export default function Activity({ recent }) {
  if (!recent.length) {
    return (
      <section className="card empty">
        <p className="muted">Your recent requests will appear here.</p>
      </section>
    );
  }
  return (
    <section className="card">
      <h3>Recent</h3>
      <ul className="activity">
        {recent.map((t) => (
          <li key={t.task_id}>
            <span className={`pulse-dot ${tone(t.outcome || t.status)}`} />
            <div className="grow">
              <div className="cmd">{t.command}</div>
              <div className="muted small">{when(t.created_at)}</div>
              {t.error && <div className="a-error">{t.error}</div>}
            </div>
            <span className={`badge ${tone(t.outcome || t.status)}`}>{t.outcome || t.status}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
