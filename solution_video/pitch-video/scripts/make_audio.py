"""Generates the film's original ambient music bed into assets/audio/music_bed.wav (numpy synthesis, deterministic).
UI sound cues live in scripts/make_sfx.py. Music is owned separately from the UI cue layer: running this
script rewrites the bed, so leave it alone if the bed is being replaced or mixed elsewhere.

    python3 scripts/make_audio.py
"""
import os, sys, wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_frames import SCENES, TOTAL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
SR, DUR = 48000, float(TOTAL)
AT = {sid: start for sid, start, *_ in SCENES}  # the bed follows the scene plan

# ---------------------------------------------------------------- music bed
N = {"A2": 110.0, "B2": 123.47, "D3": 146.83, "E3": 164.81, "F#3": 185.0, "G2": 98.0, "A3": 220.0,
     "B3": 246.94, "C#4": 277.18, "D4": 293.66, "F#4": 369.99}
CHORDS = [["D3", "A3", "D4", "F#4"], ["B2", "F#3", "B3", "D4"], ["G2", "D3", "B3", "D4"], ["A2", "E3", "A3", "C#4"]]
CHORD_LEN, XF = 8.0, 3.0
FINAL_D = float(AT["s12-close"])  # the close lands on the tonic and holds

def env_curve(points, t):
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)

def raised(n):
    return 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))

def music():
    n = int(SR * DUR)
    t = np.arange(n) / SR
    L, R = np.zeros(n), np.zeros(n)
    # chord schedule: (start, end, chord)
    sched, k = [], 0
    while k * CHORD_LEN < FINAL_D:
        sched.append((k * CHORD_LEN, min((k + 1) * CHORD_LEN, FINAL_D), CHORDS[k % 4]))
        k += 1
    sched.append((FINAL_D, DUR, CHORDS[0]))
    a4, a5, a8, a9 = AT["s04-intro"], AT["s05-intake"], AT["s08-optimize"], AT["s09-agent"]
    bright = env_curve([(0, 0), (a4, 0), (a4 + 3, 1), (a5 - 2, 1), (a5 + 1, 0), (a8, 0), (a8 + 3, 1), (a9 - 2, 1), (a9 + 1, 0), (DUR, 0)], t)
    for s, e, chord in sched:
        a, b = max(0, int((s - XF / 2) * SR)), min(n, int((e + XF / 2) * SR))
        seg = t[a:b]
        w = np.ones(b - a)
        f = min(int(XF * SR), (b - a) // 2)
        if s > 0: w[:f] *= raised(f)
        if e < DUR: w[-f:] *= raised(f)[::-1]
        for i, name in enumerate(chord):
            fr = N[name]
            v = (np.sin(2 * np.pi * fr * seg) + 0.5 * np.sin(2 * np.pi * fr * 1.003 * seg + 1.0)
                 + 0.12 * np.sin(2 * np.pi * 2 * fr * seg) + 0.18 * bright[a:b] * np.sin(2 * np.pi * 4 * fr * seg + 0.5))
            v *= w * (0.9 if i == 0 else 0.55)
            pan = [-0.35, 0.25, -0.15, 0.35][i]
            L[a:b] += v * (1 - pan) / 2
            R[a:b] += v * (1 + pan) / 2
    # soft bell arpeggio on chord tones, one note every 2 s from S02 until just before the close
    rng = np.random.default_rng(7)  # seeded: identical every run
    for j, st in enumerate(np.arange(float(AT["s02-problem"]), FINAL_D - 4, 2.0)):
        chord = CHORDS[int(st // CHORD_LEN) % 4]
        fr = N[chord[[1, 3, 2, 3][j % 4]]] * 2
        m = int(4.0 * SR); a = int(st * SR); seg = np.arange(min(m, n - a)) / SR
        v = np.sin(2 * np.pi * fr * seg) * np.exp(-seg / 1.1) * np.minimum(1, seg / 0.01) * (0.07 + 0.02 * rng.random())
        p = 0.3 if j % 2 else -0.3
        L[a:a + len(seg)] += v * (1 - p) / 2; R[a:a + len(seg)] += v * (1 + p) / 2
    # quiet air: box-filtered noise
    for ch in (L, R):
        noise = rng.standard_normal(n)
        k = np.ones(96) / 96
        ch += 0.03 * np.convolve(np.convolve(noise, k, "same"), k, "same")
    g = env_curve([(0, 0), (2, 0.55), (AT["s03-stakes"], 0.6), (AT["s04-intro"], 0.75), (AT["s05-intake"], 0.65), (AT["s08-optimize"], 0.72),
                   (AT["s09-agent"], 0.65), (AT["s11-architecture"], 0.7), (FINAL_D, 0.75), (FINAL_D + 8, 0.7), (DUR, 0)], t)
    L *= g; R *= g
    peak = max(np.abs(L).max(), np.abs(R).max())
    st = np.stack([L, R], 1) / peak * 10 ** (-3 / 20)
    with wave.open(os.path.join(OUT, "music_bed.wav"), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((st * 32767).astype("<i2").tobytes())

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    music()
    print("wrote", sorted(os.listdir(OUT)))
