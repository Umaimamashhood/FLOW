"""On-device speech-to-text (faster-whisper) and text-to-speech (pyttsx3). SRS FR-1, FR-35."""
from __future__ import annotations

import importlib.util
import io
import math
import threading
import wave

from flow import config


class VoiceUnavailable(Exception):
    pass


_model = None
_model_lock = threading.Lock()


def available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def _whisper():
    global _model
    with _model_lock:
        if _model is None:
            if not available():
                raise VoiceUnavailable(
                    "Speech recognition is not installed. In the backend folder run: "
                    "python -m pip install faster-whisper")
            from faster_whisper import WhisperModel
            _model = WhisperModel(config.WHISPER_MODEL, device="auto", compute_type="int8")
        return _model


def wav_to_samples(wav_bytes: bytes):
    """Decode 16 kHz 16-bit WAV into float samples. Done here so no audio library has to be version-matched."""
    import numpy as np

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
        if wav.getsampwidth() != 2:
            raise ValueError("expected 16-bit audio")
        if wav.getframerate() != 16000:
            raise ValueError("expected 16 kHz audio")
        channels = wav.getnchannels()
        frames = wav.readframes(wav.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples


def transcribe(wav_bytes: bytes) -> dict:
    """Return the transcript and a confidence score in [0, 1] (exp of mean segment log-probability)."""
    if config.MOCK_MODE:
        return {"text": "", "confidence": 0.0, "error": "voice is disabled in mock mode"}
    model = _whisper()  # raises VoiceUnavailable when the package is missing
    samples = wav_to_samples(wav_bytes)
    if samples.size == 0:
        return {"text": "", "confidence": 0.0}
    segments, _ = model.transcribe(samples, language="en", beam_size=1, vad_filter=True)
    segs = list(segments)
    text = " ".join(s.text.strip() for s in segs).strip()
    conf = math.exp(sum(s.avg_logprob for s in segs) / len(segs)) if segs else 0.0
    return {"text": text, "confidence": round(conf, 3)}


def speak(text: str) -> bool:
    """Speak in the background. Returns False when no offline TTS engine is installed."""
    if config.MOCK_MODE or not text.strip():
        return False
    if importlib.util.find_spec("pyttsx3") is None:
        return False

    def _say() -> None:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    threading.Thread(target=_say, daemon=True).start()
    return True
