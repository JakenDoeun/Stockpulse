/**
 * UI sound cues, synthesized with the Web Audio API (no audio files to load).
 * Cues mark real outcomes only, never button clicks; every outcome is also shown on screen.
 * The film's UI cue layer (solution_video/pitch-video/scripts/make_sfx.py) uses the same notes and envelopes.
 */
import { persist } from "./store.js";

export type Cue = "select" | "success" | "review" | "error";

// [frequency Hz, start s, decay s, level]; one soft sine voice per note plus a quiet octave for sheen
const NOTES: Record<Cue, [number, number, number, number][]> = {
  select: [[880, 0, 0.09, 0.6], [1318.5, 0.06, 0.14, 0.6]],
  success: [[659.25, 0, 0.22, 0.42], [830.61, 0.07, 0.22, 0.42], [987.77, 0.14, 0.3, 0.46]],
  review: [[587.33, 0, 0.16, 0.6], [587.33, 0.14, 0.2, 0.55]],
  error: [[523.25, 0, 0.16, 0.53], [392, 0.12, 0.26, 0.53]],
};
const RANK: Record<Cue, number> = { select: 1, success: 2, review: 3, error: 4 };
const LENGTH = (c: Cue) => Math.max(...NOTES[c].map(([, at, decay]) => at + decay * 4));
const REPEAT_MS = 1500; // the same cue again inside this window is dropped (polling, double handlers)
const KEY = "stockpulse.sfx";

type Prefs = { muted: boolean, volume: number };
let prefs: Prefs = { muted: false, volume: 0.5, ...persist.read<Partial<Prefs>>(KEY, {}) };
let ctx: AudioContext | null = null;
let out: GainNode | null = null;
let playing: { cue: Cue, until: number } | null = null;
const last: Partial<Record<Cue, number>> = {};

// Browsers only allow audio after a user gesture: create the context on the first one, never before.
const unlock = () => {
  if (!ctx) {
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AC) return;
    ctx = new AC();
    out = ctx.createGain();
    out.gain.value = level();
    out.connect(ctx.destination);
  }
  if (ctx.state === "suspended") ctx.resume().catch(() => {});
};
for (const ev of ["pointerdown", "keydown"]) window.addEventListener(ev, unlock, { capture: true, passive: true });

// perceptual curve: the slider's middle is a quiet, comfortable level
const level = () => (prefs.muted ? 0 : 0.35 * prefs.volume * prefs.volume);

export const sfxPrefs = () => ({ ...prefs });

export function setSfxPrefs(p: Partial<Prefs>) {
  prefs = { ...prefs, ...p, volume: Math.min(1, Math.max(0, p.volume ?? prefs.volume)) };
  persist.write(KEY, prefs);
  if (ctx && out) out.gain.setTargetAtTime(level(), ctx.currentTime, 0.02);
}

/** Play a cue for an outcome that has already happened. Silent when muted, before any user gesture, or when it would crowd another cue. */
export function sfx(cue: Cue) {
  if (prefs.muted || !ctx || !out || ctx.state !== "running") return;
  const now = performance.now();
  if (now - (last[cue] ?? -Infinity) < REPEAT_MS) return;
  if (playing && now < playing.until && RANK[cue] <= RANK[playing.cue]) return; // never stack; a more important outcome may cut in
  last[cue] = now;
  playing = { cue, until: now + LENGTH(cue) * 1000 };
  const t0 = ctx.currentTime + 0.005;
  for (const [f, at, decay, lvl] of NOTES[cue]) {
    for (const [mult, part] of [[1, 1], [2, 0.12]]) {
      const osc = ctx.createOscillator(), g = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = f * mult;
      g.gain.setValueAtTime(0, t0 + at);
      g.gain.linearRampToValueAtTime(lvl * part, t0 + at + 0.004);
      g.gain.setTargetAtTime(0, t0 + at + 0.004, decay);
      osc.connect(g).connect(out);
      osc.start(t0 + at);
      osc.stop(t0 + at + 0.004 + decay * 6);
    }
  }
}
