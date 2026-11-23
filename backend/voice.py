"""On-device speech to text (faster-whisper) and speech output (pyttsx3). SRS FR-1, FR-35."""
from __future__ import annotations

import importlib.util
import io
import math
import threading
import wave

import config


class VoiceUnavailable(Exception):
    pass


_model = None
_model_lock = threading.Lock()
PAD_SAMPLES = 4800      # 0.3 s of silence kept at each end
FRAME = 320             # 20 ms at 16 kHz
VOICED_LEVEL = 0.02     # frame loudness (after normalising) that counts as speech


def available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def _whisper():
    global _model
    with _model_lock:
        if _model is None:
            if not available():
                raise VoiceUnavailable(
                    "Speech recognition is not installed. In the backend folder run: "
                    "python -m pip install -r requirements.txt")
            from faster_whisper import WhisperModel
            _model = WhisperModel(config.WHISPER_MODEL, device="auto", compute_type="int8")
        return _model


def wav_to_samples(wav_bytes: bytes):
    """Decode 16 kHz 16-bit WAV into float samples."""
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


def prepare(samples):
    """Make quiet or noisy edges and uneven loudness easier to recognise.

    The volume is scaled so the loudest sound is at 90% of full scale, and silence at both ends is
    trimmed, keeping 0.3 seconds of padding so no word is cut off.
    """
    import numpy as np

    if samples.size == 0:
        return samples
    peak = float(np.max(np.abs(samples)))
    if peak < 1e-4:
        return samples[:0]
    samples = samples * (0.9 / peak)
    frames = len(samples) // FRAME
    if frames == 0:
        return samples
    energy = np.sqrt((samples[: frames * FRAME].reshape(frames, FRAME) ** 2).mean(axis=1))
    voiced = np.where(energy > VOICED_LEVEL)[0]
    if voiced.size == 0:
        return samples
    start = max(0, int(voiced[0]) * FRAME - PAD_SAMPLES)
    end = min(len(samples), (int(voiced[-1]) + 1) * FRAME + PAD_SAMPLES)
    return samples[start:end]


def transcribe(wav_bytes: bytes) -> dict:
    """Return the transcript and a confidence score in [0, 1] (exp of mean segment log-probability)."""
    if config.MOCK_MODE:
        return {"text": "", "confidence": 0.0, "error": "voice is disabled in mock mode"}
    model = _whisper()  # raises VoiceUnavailable when the package is missing
    samples = prepare(wav_to_samples(wav_bytes))
    if samples.size == 0:
        return {"text": "", "confidence": 0.0}
    segments, _ = model.transcribe(
        samples,
        language="en",
        task="transcribe",
        beam_size=5,                  # search several word options, pick the most likely
        best_of=5,
        temperature=0.0,              # no random guessing
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,
        no_speech_threshold=0.5,
    )
    segs = list(segments)
    text = " ".join(s.text.strip() for s in segs).strip()
    conf = math.exp(sum(s.avg_logprob for s in segs) / len(segs)) if segs else 0.0
    return {"text": text, "confidence": round(conf, 3)}


def speak(text: str) -> bool:
    """Speak in the background. Returns False when no offline voice engine is installed."""
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


def warmup() -> None:
    """Load the speech model in the background at startup so the first request is not slow."""
    if config.MOCK_MODE or not available():
        return
    try:
        _whisper()
    except Exception:
        pass
