const ITEMS = [
  ["assistant", "Assistant", "◎"],
  ["history", "History", "⟲"],
  ["settings", "Settings", "⚙"],
  ["help", "Help", "?"],
];

export default function Sidebar({ view, setView, online, model, ollamaError }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="logo">F</span>
        <div>
          <strong>FLOW</strong>
          <small>Your computer, by voice</small>
        </div>
      </div>

      <nav className="nav">
        {ITEMS.map(([key, label, icon]) => (
          <button key={key} className={`nav-item ${view === key ? "active" : ""}`} onClick={() => setView(key)}>
            <span className="nav-icon">{icon}</span>
            {label}
          </button>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div className={`conn ${online ? "on" : "off"}`}>
          <span className="dot" />
          {online ? "Backend connected" : "Backend offline"}
        </div>
        {online && model && <p className="muted small">Model · {model}</p>}
        {online && ollamaError && <p className="warn-text small">{ollamaError}</p>}
        {!online && <p className="muted small">Start it with <code>python main.py</code> in the backend folder.</p>}
      </div>
    </aside>
  );
}
