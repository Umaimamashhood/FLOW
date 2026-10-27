export default function ErrorBanner({ message, tone = "error", onDismiss }) {
  if (!message) return null;
  return (
    <div className={`banner ${tone}`} role="alert">
      <span>{message}</span>
      {onDismiss && <button className="link" onClick={onDismiss}>Dismiss</button>}
    </div>
  );
}
