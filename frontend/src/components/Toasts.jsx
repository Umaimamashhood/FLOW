import { useCallback, useState } from "react";

export function useToasts() {
  const [toasts, setToasts] = useState([]);
  const push = useCallback((text, tone = "info") => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((list) => [...list.slice(-3), { id, text, tone }]);
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), 5000);
  }, []);
  const dismiss = useCallback((id) => setToasts((list) => list.filter((t) => t.id !== id)), []);
  return { toasts, push, dismiss };
}

export default function Toasts({ toasts, dismiss }) {
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map((t) => (
        <button key={t.id} className={`toast ${t.tone}`} onClick={() => dismiss(t.id)}>
          {t.text}
        </button>
      ))}
    </div>
  );
}
