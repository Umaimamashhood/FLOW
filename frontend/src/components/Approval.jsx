import { useState } from "react";

// Shown when FLOW needs permission before changing something on this computer.
export default function Approval({ awaiting, onDecide }) {
  const options = awaiting.options || [];
  const [choice, setChoice] = useState(0);
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label="Approval needed">
      <div className="modal card">
        <p className="eyebrow">Approval needed</p>
        <h3>Should FLOW continue?</h3>
        <pre className="code">{awaiting.message}</pre>
        {options.length > 0 && (
          <div className="options">
            {options.map((title, i) => (
              <label key={i} className={`option ${choice === i ? "on" : ""}`}>
                <input type="radio" name="choice" checked={choice === i} onChange={() => setChoice(i)} />
                {title}
              </label>
            ))}
          </div>
        )}
        <div className="modal-actions">
          <button className="btn ghost" onClick={() => onDecide(false, null)}>Cancel</button>
          <button className="btn primary" onClick={() => onDecide(true, options.length ? choice : null)}>
            {options.length ? "Play selected" : "Approve"}
          </button>
        </div>
      </div>
    </div>
  );
}
