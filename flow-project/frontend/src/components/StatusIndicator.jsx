export default function StatusIndicator({ listening, active, awaiting }) {
  let label = "Idle";
  let tone = "idle";
  if (listening) {
    label = "Listening";
    tone = "listening";
  } else if (awaiting) {
    label = "Waiting for you";
    tone = "waiting";
  } else if (active && ["Planning", "Executing"].includes(active.status)) {
    label = "Thinking";
    tone = "thinking";
  } else if (active && active.status === "Paused") {
    label = "Paused";
    tone = "waiting";
  }
  return (
    <div className={`status ${tone}`} aria-live="polite">
      <span className="dot" /> {label}
    </div>
  );
}
