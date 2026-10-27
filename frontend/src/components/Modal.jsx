// Shared dialog layout: Cancel is always bottom-left, the primary action bottom-right.
export default function Modal({ title, children, onCancel, onConfirm, confirmLabel = "Confirm", danger = false, confirmDisabled = false }) {
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={title}>
      <div className="modal">
        <h2>{title}</h2>
        <div className="modal-body">{children}</div>
        <div className="modal-footer">
          <button className="secondary" onClick={onCancel}>Cancel</button>
          <button className={danger ? "danger" : "primary"} onClick={onConfirm} disabled={confirmDisabled}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
