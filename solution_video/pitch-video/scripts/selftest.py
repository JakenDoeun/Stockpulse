"""Assert-based self-check for the build scripts' non-trivial logic. Run: python3 scripts/selftest.py"""
import json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build, vo_timing
from gen_frames import SCENES, Cues

# 1. speech detection on a synthetic clip: 0.4 s silence, 2 s tone, 0.6 s silence
with tempfile.TemporaryDirectory() as d:
    clip = os.path.join(d, "t.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "aevalsrc='0.5*sin(2*PI*220*t)*between(t,0.4,2.4)':d=3", "-ar", "44100", clip], check=True)
    first, last, dur = vo_timing.speech_span(clip)
    assert abs(first - 0.4) < 0.08 and abs(last - 2.4) < 0.08 and abs(dur - 3.0) < 0.1, (first, last, dur)
    on = vo_timing.word_onsets("one two three four", first, last)
    assert on[0] == round(first, 3) and on == sorted(on) and on[-1] < last, on

# 2. every cue phrase resolves and every narration fits its scene window
for sid, start, dur, vo, text in SCENES:
    assert Cues(sid, vo, text).end < dur - 0.4, sid

# 3. captions: inside the film, in order, at most two lines of at most 46 characters
cues = json.load(open(os.path.join(build.ROOT, "build", "cues.json")))
caps = build.caption_cues(cues)
assert caps == sorted(caps, key=lambda c: c[0])
for a, b, lines in caps:
    assert 0 <= a < b <= max(sc['start'] + sc['duration'] for sc in cues.values()), (a, b, lines)
    assert len(lines) <= 2 and all(len(l) <= 46 for l in lines), lines
print(f"selftest ok: {len(caps)} captions")
