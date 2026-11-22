// Spoken feedback through the system's own voices. Works offline on Windows.
export function speak(text, volume = 1) {
  if (!("speechSynthesis" in window) || !text) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.volume = Math.max(0, Math.min(1, Number(volume) || 1));
  utterance.rate = 1.05;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

// Short spoken sentence: the first sentence, at most 180 characters.
export function briefly(text) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  const first = clean.split(/(?<=[.!?])\s/)[0] || clean;
  return first.length > 180 ? `${first.slice(0, 177)}…` : first;
}
