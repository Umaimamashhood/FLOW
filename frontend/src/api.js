// Every call to the FLOW backend (127.0.0.1:8765). Errors carry the backend's plain-language message.
export const BASE = "http://127.0.0.1:8765";
export const WS_URL = "ws://127.0.0.1:8765/ws";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...options });
  } catch {
    throw new Error("FLOW's backend is not running. Start it with python main.py.");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status}).`);
  return body;
}

const json = (value) => JSON.stringify(value);

export const api = {
  status: () => request("/status"),
  models: () => request("/models"),
  settings: () => request("/settings"),
  saveSettings: (values) => request("/settings", { method: "PUT", body: json(values) }),
  submit: (text, mode = "text") => request("/commands", { method: "POST", body: json({ text, mode }) }),
  tasks: (search = "", page = 1) => request(`/tasks?search=${encodeURIComponent(search)}&page=${page}`),
  task: (id) => request(`/tasks/${id}`),
  remove: (id) => request(`/tasks/${id}`, { method: "DELETE" }),
  clearHistory: () => request("/history/clear", { method: "POST" }),
  pause: (id) => request(`/tasks/${id}/pause`, { method: "POST" }),
  resume: (id) => request(`/tasks/${id}/resume`, { method: "POST" }),
  abort: (id) => request(`/tasks/${id}/abort`, { method: "POST" }),
  confirm: (id, approved, choice = null) =>
    request(`/tasks/${id}/confirm`, { method: "POST", body: json({ approved, choice }) }),
  transcribe: async (wavBlob) => {
    const res = await fetch(BASE + "/voice/transcribe", {
      method: "POST",
      headers: { "Content-Type": "audio/wav" },
      body: wavBlob,
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || "Speech recognition failed.");
    return body;
  },
  exportHistory: async () => {
    const res = await fetch(BASE + "/export");
    if (!res.ok) throw new Error("Export failed.");
    return res.blob();
  },
};
