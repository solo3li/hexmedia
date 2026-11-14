// Procedural Sound Design & BGM Presets
// Lightweight 16-bit PCM WAV data URI generator with zero external dependencies

function createWavDataUri(sampleRate: number, samples: Float32Array): string {
  const numSamples = samples.length;
  const headerBytes = 44;
  const totalLength = headerBytes + numSamples * 2;
  const buffer = new Uint8Array(totalLength);
  const view = new DataView(buffer.buffer);

  // RIFF identifier
  view.setUint8(0, 0x52); // 'R'
  view.setUint8(1, 0x49); // 'I'
  view.setUint8(2, 0x46); // 'F'
  view.setUint8(3, 0x46); // 'F'
  view.setUint32(4, 36 + numSamples * 2, true); // file size - 8
  // WAVE
  view.setUint8(8, 0x57);  // 'W'
  view.setUint8(9, 0x41);  // 'A'
  view.setUint8(10, 0x56); // 'V'
  view.setUint8(11, 0x45); // 'E'
  // 'fmt ' chunk
  view.setUint8(12, 0x66); // 'f'
  view.setUint8(13, 0x6d); // 'm'
  view.setUint8(14, 0x74); // 't'
  view.setUint8(15, 0x20); // ' '
  view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true);  // AudioFormat (1 for PCM)
  view.setUint16(22, 1, true);  // NumChannels (1 mono)
  view.setUint32(24, sampleRate, true); // SampleRate
  view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * NumChannels * BitsPerSample/8)
  view.setUint16(32, 2, true);  // BlockAlign (NumChannels * BitsPerSample/8)
  view.setUint16(34, 16, true); // BitsPerSample (16 bits)
  // 'data' chunk
  view.setUint8(36, 0x64); // 'd'
  view.setUint8(37, 0x61); // 'a'
  view.setUint8(38, 0x74); // 't'
  view.setUint8(39, 0x61); // 'a'
  view.setUint32(40, numSamples * 2, true);

  // Write PCM audio data
  let offset = 44;
  for (let i = 0; i < numSamples; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    const val = s < 0 ? s * 0x8000 : s * 0x7fff;
    view.setInt16(offset, val, true);
    offset += 2;
  }

  // Convert Uint8Array to base64 with zero dependencies
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  let base64 = "";
  const len = buffer.byteLength;
  for (let i = 0; i < len; i += 3) {
    const b0 = buffer[i];
    const b1 = i + 1 < len ? buffer[i + 1] : 0;
    const b2 = i + 2 < len ? buffer[i + 2] : 0;

    base64 += chars[b0 >> 2];
    base64 += chars[((b0 & 3) << 4) | (b1 >> 4)];
    base64 += i + 1 < len ? chars[((b1 & 15) << 2) | (b2 >> 6)] : "=";
    base64 += i + 2 < len ? chars[b2 & 63] : "=";
  }

  return `data:audio/wav;base64,${base64}`;
}

// Caches for generated audio data URIs
const sfxCache: Record<string, string> = {};
const bgmCache: Record<string, string> = {};

/**
 * Generates an energetic whoosh transition SFX (frequency sweep with noise texture)
 */
export function getWhooshSfxDataUri(): string {
  if (sfxCache.whoosh) return sfxCache.whoosh;

  const sampleRate = 16000;
  const duration = 0.28;
  const numSamples = Math.floor(sampleRate * duration);
  const samples = new Float32Array(numSamples);

  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    const progress = t / duration;
    // Frequency rises then falls
    const freq = 200 + Math.sin(progress * Math.PI) * 1100;
    // Envelope: quick attack, parabolic body, smooth decay
    const env = Math.sin(progress * Math.PI) ** 1.6;
    // Mixed sine with pseudo-pink noise
    const noise = (Math.sin(i * 123.45) % 1) * 0.45;
    const tone = Math.sin(2 * Math.PI * freq * t) * 0.55;
    samples[i] = (tone + noise) * env * 0.85;
  }

  sfxCache.whoosh = createWavDataUri(sampleRate, samples);
  return sfxCache.whoosh;
}

/**
 * Generates a clean pop SFX (snappy pitch drop)
 */
export function getPopSfxDataUri(): string {
  if (sfxCache.pop) return sfxCache.pop;

  const sampleRate = 16000;
  const duration = 0.08;
  const numSamples = Math.floor(sampleRate * duration);
  const samples = new Float32Array(numSamples);

  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    const progress = t / duration;
    // Rapid pitch drop 480Hz -> 120Hz
    const freq = 480 * Math.exp(-progress * 5.0) + 120;
    const env = Math.exp(-progress * 14.0);
    samples[i] = Math.sin(2 * Math.PI * freq * t) * env * 0.9;
  }

  sfxCache.pop = createWavDataUri(sampleRate, samples);
  return sfxCache.pop;
}

/**
 * Generates a crisp click SFX
 */
export function getClickSfxDataUri(): string {
  if (sfxCache.click) return sfxCache.click;

  const sampleRate = 16000;
  const duration = 0.04;
  const numSamples = Math.floor(sampleRate * duration);
  const samples = new Float32Array(numSamples);

  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    const progress = t / duration;
    const freq = 900 * Math.exp(-progress * 8.0);
    const env = Math.exp(-progress * 25.0);
    samples[i] = Math.sin(2 * Math.PI * freq * t) * env * 0.8;
  }

  sfxCache.click = createWavDataUri(sampleRate, samples);
  return sfxCache.click;
}

/**
 * Generates procedural royalty-free background music loops
 */
export function getBgmDataUri(preset: string): string {
  if (bgmCache[preset]) return bgmCache[preset];

  const sampleRate = 11025; // Compact audio footprint (~66KB for 3s loop)
  const duration = 3.2; // Seamless short musical loop
  const numSamples = Math.floor(sampleRate * duration);
  const samples = new Float32Array(numSamples);

  let chordFrequencies: number[][] = [];
  if (preset === "cinematic_warm") {
    // Warm Cmaj7 -> Am9 chords (261.63, 329.63, 392.00, 493.88)
    chordFrequencies = [
      [261.63, 329.63, 392.00, 493.88],
      [220.00, 261.63, 329.63, 392.00],
    ];
  } else if (preset === "cyber_ambient") {
    // Cyber Ambient 5th interval detuned pads (110.0, 164.81, 220.0, 329.63)
    chordFrequencies = [
      [110.0, 164.81, 220.0, 329.63],
      [130.81, 196.0, 261.63, 392.0],
    ];
  } else if (preset === "lofi_chill") {
    // Lo-Fi mellow jazz progression (174.61, 220.0, 261.63, 349.23)
    chordFrequencies = [
      [174.61, 220.0, 261.63, 349.23],
      [146.83, 174.61, 220.0, 293.66],
    ];
  } else {
    // energetic_hook: rhythmic pulse in E minor (164.81, 196.00, 246.94)
    chordFrequencies = [
      [164.81, 196.00, 246.94],
      [146.83, 174.61, 220.00],
    ];
  }

  const half = numSamples / 2;
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    const chord = i < half ? chordFrequencies[0] : chordFrequencies[1];
    let sum = 0;

    for (const freq of chord) {
      // Gentle sine tone with slight detune
      sum += Math.sin(2 * Math.PI * freq * t) * 0.22;
      sum += Math.sin(2 * Math.PI * (freq * 1.003) * t) * 0.12;
    }

    // Smooth loop envelope at boundaries
    const loopFade = Math.sin((i / numSamples) * Math.PI) ** 0.3;
    samples[i] = sum * loopFade * 0.7;
  }

  bgmCache[preset] = createWavDataUri(sampleRate, samples);
  return bgmCache[preset];
}
