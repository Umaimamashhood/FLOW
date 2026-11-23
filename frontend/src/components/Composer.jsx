import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Recorder } from "../audio";

// The main input. Click the mic (or press Ctrl+Space) to talk; FLOW sends your words when you pause.
export default function Composer({ draft, setDraft, busy, listening, setListening, onError, onSubmitted }) {
  const recorder = useRef(null);
  const stopRef = useRef(() => {});
  const [heard, setHeard] = useState("");

  const start = () => {
    if (busy || recorder.current) return;
    const rec = new Recorder({ onAutoStop: () => stopRef.current() });
    recorder.current = rec;
    setListening(true);
    rec.start().catch(() => {
      recorder.current = null;
      setListening(false);
      onError("The microphone is not available. Check the device and Windows microphone permission.");
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
        setHeard("");
        onError("I didn't catch anything. Click the mic and speak clearly.");
        return;
      }
      setHeard("Listening to what you said…");
      const result = await api.transcribe(wav);
      if (!result.text) {
        setHeard("");
        onError("No speech was recognised. Try again, closer to the microphone.");
        return;
      }
      setHeard(`I heard: “${result.text}”`);
      setDraft("");
      const task = await api.submit(result.text, "voice");
      onSubmitted(task);
    } catch (err) {
      setHeard("");
      onError(err.message || String(err));
    }
  };
  stopRef.current = stop;

  const toggle = () => {
    if (recorder.current) stop();
    else start();
  };

  // Ctrl+Space toggles the microphone from anywhere in the window.
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
    if (!text || busy) return;
    try {
      const task = await api.submit(text, "text");
      setDraft("");
      setHeard("");
      onSubmitted(task);
    } catch (err) {
      onError(err.message || String(err));
    }
  };

  return (
    <>
      <form className={`composer ${listening ? "is-listening" : ""}`} onSubmit={submit}>
        <input
          aria-label="Command"
          value={draft}
          disabled={busy}
          placeholder={
            busy ? "FLOW is working on your request…"
              : listening ? "Listening… pause when you're done"
              : "Type a request, or click the mic and speak"
          }
          onChange={(e) => setDraft(e.target.value)}
        />
        <button
          type="button"
          className={`mic-orb ${listening ? "live" : ""}`}
          aria-label={listening ? "Stop listening" : "Start listening"}
          title={listening ? "Click to send now" : "Click to talk (or press Ctrl+Space)"}
          disabled={busy}
          onClick={toggle}
        >
          <span className="ring" />
          <span className="ring r2" />
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <rect x="9" y="3" width="6" height="11" rx="3" />
            <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
          </svg>
        </button>
        <button type="submit" className="btn primary send" disabled={busy || !draft.trim()}>Send</button>
      </form>
      {heard && <p className="heard">{heard}</p>}
    </>
  );
}
