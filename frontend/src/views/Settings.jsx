import { useEffect, useState } from "react";
import { api } from "../api";

const POLICIES = ["Always Confirm", "Confirm Destructive Only", "Unattended"];
const ENGINES = ["google", "bing", "duckduckgo"];

export default function Settings({ onError, onSaved }) {
  const [form, setForm] = useState(null);
  const [models, setModels] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.settings().then(setForm).catch((e) => onError(e.message));
    api.models().then((r) => setModels(r.models)).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!form) return <div className="page"><p className="muted">Loading settings…</p></div>;

  // Only show controls for settings the backend reports, so nothing unknown is ever sent back.
  const has = (key) => Object.prototype.hasOwnProperty.call(form, key);
  const set = (key, value) => setForm({ ...form, [key]: value });

  const save = async () => {
    setSaving(true);
    try {
      setForm(await api.saveSettings(form));
      onSaved("Settings saved");
    } catch (e) {
      onError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Preferences</p>
          <h1>Settings</h1>
        </div>
        <button className="btn primary" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save changes"}</button>
      </header>

      <div className="grid-2">
        <section className="card">
          <h3>Assistant</h3>
          {has("ollama_model") && (
            <Field label="Language model">
              <select value={form.ollama_model} onChange={(e) => set("ollama_model", e.target.value)}>
                {[...new Set([form.ollama_model, ...models])].map((m) => <option key={m}>{m}</option>)}
              </select>
            </Field>
          )}
          {has("search_engine") && (
            <Field label="Search engine">
              <select value={form.search_engine} onChange={(e) => set("search_engine", e.target.value)}>
                {ENGINES.map((e) => <option key={e} value={e}>{e}</option>)}
              </select>
            </Field>
          )}
          {has("default_projects_dir") && (
            <Field label="Projects folder">
              <input value={form.default_projects_dir} onChange={(e) => set("default_projects_dir", e.target.value)} />
            </Field>
          )}
        </section>

        <section className="card">
          <h3>Voice</h3>
          {has("voice_output") && (
            <Toggle label="Speak results aloud" checked={form.voice_output} onChange={(v) => set("voice_output", v)} />
          )}
          {has("voice_volume") && (
            <Field label={`Voice volume · ${Math.round(form.voice_volume * 100)}%`}>
              <input type="range" min="0" max="1" step="0.05" value={form.voice_volume}
                     onChange={(e) => set("voice_volume", parseFloat(e.target.value))} />
            </Field>
          )}
          {has("asr_confidence_min") && (
            <Field label="Speech confidence threshold">
              <input type="number" min="0" max="1" step="0.05" value={form.asr_confidence_min}
                     onChange={(e) => set("asr_confidence_min", parseFloat(e.target.value))} />
            </Field>
          )}
        </section>

        <section className="card">
          <h3>Safety</h3>
          {has("confirmation_policy") && (
            <Field label="Approval policy">
              <select value={form.confirmation_policy} onChange={(e) => set("confirmation_policy", e.target.value)}>
                {POLICIES.map((p) => <option key={p}>{p}</option>)}
              </select>
            </Field>
          )}
          {has("auto_run_programs") && (
            <Toggle label="Run programs in the projects folder without asking" checked={form.auto_run_programs}
                    onChange={(v) => set("auto_run_programs", v)} />
          )}
          {has("history_enabled") && (
            <Toggle label="Keep a history of requests" checked={form.history_enabled}
                    onChange={(v) => set("history_enabled", v)} />
          )}
        </section>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={!!checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="track"><span className="knob" /></span>
      <span>{label}</span>
    </label>
  );
}
