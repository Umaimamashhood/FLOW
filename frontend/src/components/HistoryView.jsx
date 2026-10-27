import { useEffect, useState } from "react";
import { api } from "../api";
import Modal from "./Modal";

const PAGE_SIZE = 50;

export default function HistoryView({ onBack, onError }) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState([]);
  const [confirmClear, setConfirmClear] = useState(false);

  const load = () => api.tasks(search, page).then(setRows).catch(onError);
  useEffect(() => { load(); }, [search, page]); // eslint-disable-line react-hooks/exhaustive-deps

  const remove = async (id) => {
    try {
      await api.remove(id);
      load();
    } catch (err) {
      onError(err);
    }
  };
  const clearAll = async () => {
    setConfirmClear(false);
    try {
      await api.clearHistory();
      setPage(1);
      load();
    } catch (err) {
      onError(err);
    }
  };

  return (
    <section className="panel wide">
      <div className="toolbar">
        <button className="secondary" onClick={onBack}>Back</button>
        <input
          aria-label="Search history"
          placeholder="Search commands"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <button className="danger" onClick={() => setConfirmClear(true)}>Clear all</button>
      </div>
      <table>
        <thead>
          <tr><th>Date and time</th><th>Command</th><th>Outcome</th><th /></tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.task_id}>
              <td>{new Date(t.created_at).toLocaleString()}</td>
              <td>{t.command}</td>
              <td className={`outcome ${t.outcome || "running"}`}>{t.outcome || t.status}</td>
              <td><button className="link danger-text" onClick={() => remove(t.task_id)}>Delete</button></td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={4} className="muted">No tasks found.</td></tr>}
        </tbody>
      </table>
      <div className="toolbar">
        <button className="secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
        <span>Page {page}</span>
        <button className="secondary" disabled={rows.length < PAGE_SIZE} onClick={() => setPage(page + 1)}>Next</button>
      </div>
      {confirmClear && (
        <Modal title="Clear all history?" confirmLabel="Clear all" danger
               onCancel={() => setConfirmClear(false)} onConfirm={clearAll}>
          <p>This permanently deletes every saved task and its log. It cannot be undone.</p>
        </Modal>
      )}
    </section>
  );
}
