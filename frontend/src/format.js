// Small shared helpers for labels and colours.
export function tone(status) {
  if (status === "Completed") return "ok";
  if (status === "Failed" || status === "Aborted") return "bad";
  if (status === "Paused" || status === "Awaiting Confirmation") return "warn";
  return "live";
}

export function when(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  const today = new Date();
  const sameDay = date.toDateString() === today.toDateString();
  return sameDay
    ? date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : date.toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

// Statuses after which a task will not change again.
export const TERMINAL = ["Completed", "Failed"];
