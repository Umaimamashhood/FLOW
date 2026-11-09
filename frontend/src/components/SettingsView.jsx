import { useEffect, useState } from "react";
import { api } from "../api";

const POLICIES = ["Always Confirm", "Confirm Destructive Only", "Unattended"];

export default function SettingsView({ onBack, onError }) {
  const [form, setForm] = useState(null);
  const [models, setModels] = useState([]);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    api.settings().then(setForm).catch(onError);
    api.models().then((r) => setModels(r.models)).catch(() => setModels([]));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!form) return <section className="panel"><p className="muted">Loading settings…</p></section>;

  const set = (key, value) => setForm({ ...form, [key]: value });

  const save = async () => {
    try {
      setForm(await api.saveSettings(form));
      setSaved("Settings saved.");
    } catch (err) {
      onError(err);
    }
  };

  const exportHistory = async () => {
    try {
      const blob = await api.exportHistory();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "flow-export.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      onError(err);
    }
  };

  return (
    <section className="panel wide">
      <h2>Settings</h2>
      <div className="form">
        <label>Default projects folder
          <input value={form.default_projects_dir} onChange={(e) => set("default_projects_dir", e.target.value)} />
        </label>
        <label>Ollama model
          <select value={form.ollama_model} onChange={(e) => set("ollama_model", e.target.value)}>
            {[...new Set([form.ollama_model, ...models])].map((m) => <option key={m}>{m}</option>)}
          </select>
        </label>
        <label>Search engine
          <select value={form.search_engine} onChange={(e) => set("search_engine", e.target.value)}>
            <option value="google">Google</option>
            <option value="bing">Bing</option>
            <option value="duckduckgo">DuckDuckGo</option>
          </select>
        </label>
        <label>Coding language
          <select value={form.coding_language} onChange={(e) => set("coding_language", e.target.value)}>
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
          </select>
        </label>
        <label>Confirmation policy
          <select value={form.confirmation_policy} onChange={(e) => set("confirmation_policy", e.target.value)}>
            {POLICIES.map((p) => <option key={p}>{p}</option>)}
          </select>
        </label>
        <label>Speech confidence threshold
          <input type="number" step="0.05" min="0" max="1" value={form.asr_confidence_min}
                 onChange={(e) => set("asr_confidence_min", parseFloat(e.target.value))} />
        </label>
        <label className="check">
          <input type="checkbox" checked={form.voice_output} onChange={(e) => set("voice_output", e.target.checked)} />
          Speak results aloud
        </label>
        <label className="check">
          <input type="checkbox" checked={form.history_enabled} onChange={(e) => set("history_enabled", e.target.checked)} />
          Save task history
        </label>
        <label>Wake word <span className="muted">(not available in this version)</span>
          <input disabled value={form.wake_word} placeholder="Off" />
        </label>
      </div>
      {form.confirmation_policy === "Unattended" && (
        <p className="banner warning">Unattended mode deletes, moves and overwrites files without asking. Program runs still ask.</p>
      )}
      <div className="toolbar">
        <button className="secondary" onClick={onBack}>Back</button>
        <button className="secondary" onClick={exportHistory}>Export history (JSON)</button>
        <button className="primary" onClick={save}>Save</button>
        {saved && <span className="muted">{saved}</span>}
      </div>
    </section>
  );
}
