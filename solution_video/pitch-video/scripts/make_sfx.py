"""Generates the film's UI sound cues into assets/audio/ui_*.wav (original, numpy synthesis, deterministic).

The notes and envelopes match the app's own cues (frontend/src/lib/sfx.ts), so the film sounds like the product.
`tap` is film-only: it marks a visible cursor click on a real control. Music and voice-over are not touched here.

    python3 scripts/make_sfx.py
"""
import os, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
SR = 48000
PEAK_DBFS = -12.0  # the loudest cue; every cue keeps its designed level relative to it

# [frequency Hz, start s, decay s, level]: same table as frontend/src/lib/sfx.ts
NOTES = {
    "tap": [(1200, 0, 0.012, 0.55)],
    "select": [(880, 0, 0.09, 0.6), (1318.5, 0.06, 0.14, 0.6)],
    "success": [(659.25, 0, 0.22, 0.42), (830.61, 0.07, 0.22, 0.42), (987.77, 0.14, 0.3, 0.46)],
    "review": [(587.33, 0, 0.16, 0.6), (587.33, 0.14, 0.2, 0.55)],
    "error": [(523.25, 0, 0.16, 0.53), (392, 0.12, 0.26, 0.53)],
}

def synth(notes):
    end = max(at + 0.004 + decay * 6 for _, at, decay, _ in notes)
    t = np.arange(int(end * SR) + 1) / SR
    y = np.zeros_like(t)
    for f, at, decay, lvl in notes:
        u = t - at
        env = np.where(u < 0, 0, np.where(u < 0.004, u / 0.004, np.exp(-(u - 0.004) / decay)))  # 4 ms attack, exponential decay
        y += lvl * env * (np.sin(2 * np.pi * f * u) + 0.12 * np.sin(2 * np.pi * 2 * f * u))
    y[-int(0.003 * SR):] *= np.linspace(1, 0, int(0.003 * SR))  # no click at the cut
    return y

def main():
    cues = {k: synth(v) for k, v in NOTES.items()}
    scale = 10 ** (PEAK_DBFS / 20) / max(np.abs(y).max() for y in cues.values())
    for k, y in cues.items():
        st = np.repeat((y * scale)[:, None], 2, 1)
        with wave.open(os.path.join(OUT, f"ui_{k}.wav"), "wb") as f:
            f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
            f.writeframes((st * 32767).astype("<i2").tobytes())
        print(f"ui_{k}.wav  {len(y) / SR:.2f}s  peak {20 * np.log10(np.abs(y * scale).max()):.1f} dBFS")

if __name__ == "__main__":
    main()
