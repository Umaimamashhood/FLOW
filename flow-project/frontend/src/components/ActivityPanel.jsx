import { useState } from "react";
import { api } from "../api";

// Recent commands. Click one to see each step and what it produced.
export default function ActivityPanel({ recent, active }) {
  const [openId, setOpenId] = useState(null);
  const [detail, setDetail] = useState(null);
  const when = (iso) => (iso ? new Date(iso).toLocaleTimeString() : "");

  const toggle = async (id) => {
    if (openId === id) {
      setOpenId(null);
      setDetail(null);
      return;
    }
    setOpenId(id);
    setDetail(null);
    try {
      setDetail(await api.task(id));
    } catch (err) {
      setDetail({ error: err.message });
    }
  };

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
          <li key={t.task_id} className="clickable" onClick={() => toggle(t.task_id)}>
            <span className="time">{when(t.created_at)}</span>
            <span className="cmd">{t.command}</span>
            <span className={`outcome ${t.outcome || "running"}`}>{t.outcome || t.status}</span>
            {t.error && <div className="result">{t.error}</div>}
            {openId === t.task_id && (
              <div className="detail" onClick={(e) => e.stopPropagation()}>
                {!detail && <p className="muted">Loading…</p>}
                {detail?.error && <p className="banner error">{detail.error}</p>}
                {detail?.subtasks?.map((s) => (
                  <div key={s.subtask_id} className={`detail-step ${s.status}`}>
                    <strong>{s.agent}</strong> · {s.action.replace(/_/g, " ")} · <span>{s.status}</span>
                    {s.result && <pre>{s.result}</pre>}
                  </div>
                ))}
              </div>
            )}
          </li>
        ))}
        {recent.length === 0 && !active && <li className="muted">Nothing yet. Try “open gmail” or “play a song”.</li>}
      </ul>
    </section>
  );
}
