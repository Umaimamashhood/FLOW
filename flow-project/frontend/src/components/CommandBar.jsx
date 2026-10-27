import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Recorder } from "../audio";

// Voice: press the mic button or Ctrl+Space once, speak, and the command is sent when you stop talking.
// Typed commands are sent with Enter or Send (FR-1, FR-2, FR-3).
export default function CommandBar({ disabled, draft, setDraft, listening, setListening, onError }) {
  const recorder = useRef(null);
  const [note, setNote] = useState("");

  const finish = async () => {
    const rec = recorder.current;
    if (!rec) return;
    recorder.current = null;
    setListening(false);
    try {
      const wav = await rec.stop();
      if (!wav) {
        onError(new Error("I didn't hear any speech. Speak after the mic turns red."));
        return;
      }
      const result = await api.transcribe(wav);
      if (!result.text) {
        onError(new Error("No speech was recognised. Try again, a little closer to the microphone."));
        return;
      }
      if (result.needs_review) {  // unsure of the words: show them, do not run them
        setDraft(result.text);
        setNote("I'm not sure I heard that correctly. Check the text, then press Send.");
        return;
      }
      setNote("");
      await api.submit(result.text, "voice");
    } catch (err) {
      onError(err);
    }
  };

  const start = () => {
    if (disabled || recorder.current) return;
    const rec = new Recorder(() => finish());
    recorder.current = rec;
    setListening(true);
    rec.start().catch(() => {
      recorder.current = null;
      setListening(false);
      onError(new Error("The microphone is not available. Check the device and the microphone permission."));
    });
  };

  const toggle = () => (recorder.current ? finish() : start());

  useEffect(() => {
    const onKey = (e) => {
      if (e.ctrlKey && e.code === "Space" && !e.repeat) {
        e.preventDefault();
        toggle();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const submit = async (e) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || disabled) return;
    try {
      await api.submit(text, "text");
      setDraft("");
      setNote("");
    } catch (err) {
      onError(err);
    }
  };

  return (
    <div className="command-bar">
      <form onSubmit={submit}>
        <input
          aria-label="Command"
          placeholder={disabled ? "A task is running…" : "Type a command, e.g. open gmail"}
          value={draft}
          disabled={disabled}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button
          type="button"
          className={`mic ${listening ? "live" : ""}`}
          aria-label="Talk"
          title="Click or press Ctrl+Space, speak, and it sends when you stop"
          disabled={disabled && !listening}
          onClick={toggle}
        >
          🎙
        </button>
        <button type="submit" className="primary" disabled={disabled || !draft.trim()}>Send</button>
      </form>
      {listening && <p className="hint">Listening… speak, and it will send when you stop.</p>}
      {note && <p className="hint">{note}</p>}
    </div>
  );
}
