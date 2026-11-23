import { useEffect, useState } from "react";
import { api } from "../api";
import { tone, when } from "../format";

const PAGE = 50;

export default function History({ onError }) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState([]);
  const [askClear, setAskClear] = useState(false);

  const load = () => api.tasks(search, page).then(setRows).catch((e) => onError(e.message));
  useEffect(() => { load(); }, [search, page]); // eslint-disable-line react-hooks/exhaustive-deps

  const remove = async (id) => {
    try { await api.remove(id); load(); } catch (e) { onError(e.message); }
  };
  const clear = async () => {
    setAskClear(false);
    try { await api.clearHistory(); setPage(1); load(); } catch (e) { onError(e.message); }
  };
  const exportAll = async () => {
    try {
      const blob = await api.exportHistory();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "flow-history.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) { onError(e.message); }
  };

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Your work</p>
          <h1>History</h1>
        </div>
        <div className="row gap">
          <button className="btn ghost" onClick={exportAll}>Export</button>
          <button className="btn danger" onClick={() => setAskClear(true)}>Clear all</button>
        </div>
      </header>

      <input className="search" placeholder="Search your requests…" value={search}
             onChange={(e) => { setSearch(e.target.value); setPage(1); }} />

      <section className="card list">
        {rows.length === 0 && <p className="muted">No requests found.</p>}
        {rows.map((t) => (
          <div key={t.task_id} className="row-item">
            <div className="grow">
              <div className="cmd">{t.command}</div>
              <div className="muted small">{when(t.created_at)}</div>
              {t.error && <div className="a-error">{t.error}</div>}
            </div>
            <span className={`badge ${tone(t.outcome || t.status)}`}>{t.outcome || t.status}</span>
            <button className="btn icon" title="Delete" onClick={() => remove(t.task_id)}>✕</button>
          </div>
        ))}
      </section>

      <div className="pager">
        <button className="btn ghost" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
        <span className="muted">Page {page}</span>
        <button className="btn ghost" disabled={rows.length < PAGE} onClick={() => setPage(page + 1)}>Next</button>
      </div>

      {askClear && (
        <div className="overlay" role="dialog" aria-modal="true">
          <div className="modal card">
            <h3>Clear all history?</h3>
            <p className="muted">Every saved request will be deleted. This can't be undone.</p>
            <div className="modal-actions">
              <button className="btn ghost" onClick={() => setAskClear(false)}>Cancel</button>
              <button className="btn danger" onClick={clear}>Clear all</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
