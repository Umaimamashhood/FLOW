import { useState } from "react";
import Composer from "../components/Composer";
import TaskCard from "../components/TaskCard";
import Activity from "../components/Activity";
import { Understood, Outcome, isWorking } from "../components/Feedback";

const SUGGESTIONS = [
  "open gmail",
  "play shape of you",
  "make a calculator and run it",
  "open chatgpt and ask it to explain recursion",
  "increase the volume",
  "open file explorer",
];

export default function Assistant({ active, latest, busy, recent, onError, onSubmitted, onDismiss }) {
  const [draft, setDraft] = useState("");
  const [listening, setListening] = useState(false);

  // What to show under the composer: live progress, the plan, or the final result.
  let panel = null;
  if (active) panel = <TaskCard task={active} onError={onError} />;
  else if (isWorking(latest)) panel = <Understood task={latest} />;
  else if (latest) panel = <Outcome task={latest} onClose={onDismiss} />;

  return (
    <div className="page">
      <section className="hero">
        <h1>What should FLOW do?</h1>
        <p className="muted">A Voice-Driven Multi-Agent Coding Assistant</p>
      </section>

      <Composer
        draft={draft}
        setDraft={setDraft}
        busy={busy}
        listening={listening}
        setListening={setListening}
        onError={onError}
        onSubmitted={onSubmitted}
      />

      <div className="chips">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chip" disabled={busy} onClick={() => setDraft(s)}>{s}</button>
        ))}
      </div>

      {panel}
      <Activity recent={recent} />
    </div>
  );
}
