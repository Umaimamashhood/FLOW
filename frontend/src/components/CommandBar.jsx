import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Recorder } from "../audio";

// Text entry plus push-to-talk: hold the mic button or Ctrl+Space (FR-1, FR-2, FR-3, FR-4).
export default function CommandBar({ disabled, draft, setDraft, listening, setListening, onError }) {
  const recorder = useRef(null);
  const [note, setNote] = useState("");

  const start = () => {
    if (disabled || recorder.current) return;
    const rec = new Recorder();
    recorder.current = rec;
    setListening(true);
    rec.start().catch(() => {
      recorder.current = null;
      setListening(false);
      onError(new Error("The microphone is not available. Check the device and the microphone permission."));
    });
  };

  const stop = async () => {
    const rec = recorder.current;
    if (!rec) return;
    recorder.current = null;
    setListening(false);
    try {
      const wav = await rec.stop();
      if (!wav) {
        onError(new Error("That was too short. Hold the button while you speak."));
        return;
      }
      const result = await api.transcribe(wav);
      if (!result.text) {
        onError(new Error("No speech was recognised. Try again, a little closer to the microphone."));
        return;
      }
      if (result.needs_review) {
        setDraft(result.text);
        setNote("Low recognition confidence. Check the text, then press Send.");
      } else {
        setNote("");
        setDraft("");
        await api.submit(result.text, "voice");
      }
    } catch (err) {
      onError(err);
    }
  };

  useEffect(() => {
    const down = (e) => {
      if (e.ctrlKey && e.code === "Space" && !e.repeat) {
        e.preventDefault();
        start();
      }
    };
    const up = (e) => {
      if (e.code === "Space" || e.key === "Control") stop();
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
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
          aria-label="Hold to talk"
          title="Hold to talk (or hold Ctrl+Space)"
          disabled={disabled}
          onPointerDown={start}
          onPointerUp={stop}
          onPointerLeave={stop}
        >
          🎙
        </button>
        <button type="submit" className="primary" disabled={disabled || !draft.trim()}>Send</button>
      </form>
      {note && <p className="hint">{note}</p>}
    </div>
  );
}
