// Microphone capture: records raw PCM at 16 kHz, ends automatically when speech stops, and writes a 16-bit mono WAV.
// No browser decoding is needed, so compressed-format errors cannot occur.

export const MIN_SECONDS = 0.4;
const SPEECH_LEVEL = 0.015;   // loudness that counts as speech
const END_SILENCE_MS = 1200;  // silence after speech that ends the recording
const NO_SPEECH_MS = 8000;    // give up if nothing is said
const MAX_MS = 20000;         // hard limit

export class Recorder {
  constructor(onAutoStop) {
    this.onAutoStop = onAutoStop;
    this.chunks = [];
    this.ready = null;
    this.heardSpeech = false;
    this.finished = false;
  }

  start() {
    this.ready = (async () => {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      this.ctx = new AudioContext();
      const source = this.ctx.createMediaStreamSource(this.stream);
      this.processor = this.ctx.createScriptProcessor(4096, 1, 1);
      this.startedAt = performance.now();
      this.lastSpeech = this.startedAt;
      this.processor.onaudioprocess = (e) => this.onAudio(e.inputBuffer.getChannelData(0));
      source.connect(this.processor);
      this.processor.connect(this.ctx.destination);
    })();
    return this.ready;
  }

  onAudio(data) {
    this.chunks.push(new Float32Array(data));
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
    const level = Math.sqrt(sum / data.length);
    const now = performance.now();
    if (level > SPEECH_LEVEL) {
      this.heardSpeech = true;
      this.lastSpeech = now;
    }
    const elapsed = now - this.startedAt;
    const done =
      (this.heardSpeech && now - this.lastSpeech > END_SILENCE_MS) ||
      (!this.heardSpeech && elapsed > NO_SPEECH_MS) ||
      elapsed > MAX_MS;
    if (done && !this.finished && this.onAutoStop) {
      this.finished = true;
      this.onAutoStop();
    }
  }

  // Resolves to a WAV blob, or null when the recording was too short to be speech.
  async stop() {
    await this.ready;
    this.processor.disconnect();
    this.stream.getTracks().forEach((t) => t.stop());
    const rate = this.ctx.sampleRate;
    const total = this.chunks.reduce((n, c) => n + c.length, 0);
    const samples = new Float32Array(total);
    let offset = 0;
    for (const chunk of this.chunks) {
      samples.set(chunk, offset);
      offset += chunk.length;
    }
    await this.ctx.close();
    if (!this.heardSpeech || total / rate < MIN_SECONDS) return null;
    const resampled = await resampleTo16k(samples, rate);
    return encodeWav(resampled, 16000);
  }
}

async function resampleTo16k(samples, rate) {
  if (rate === 16000) return samples;
  const length = Math.ceil((samples.length * 16000) / rate);
  const offline = new OfflineAudioContext(1, length, 16000);
  const buffer = offline.createBuffer(1, samples.length, rate);
  buffer.copyToChannel(samples, 0);
  const source = offline.createBufferSource();
  source.buffer = buffer;
  source.connect(offline.destination);
  source.start();
  const rendered = await offline.startRendering();
  return rendered.getChannelData(0);
}

function writeString(view, offset, text) {
  for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i));
}

function encodeWav(samples, rate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}
