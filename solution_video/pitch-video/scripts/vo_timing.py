"""Times the picture to the real ElevenLabs clips: writes build/vo_words.json (word onsets per clip)
and reports any clip that is too long for its scene. Run before regenerating and re-rendering.

    python3 scripts/vo_timing.py
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_frames import SCENES, ROOT, VO_OFFSET, estimate_words

def speech_span(path):
    """(first, last, duration): first and last moment of speech in the clip, via FFmpeg silence detection."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "silencedetect=n=-45dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True, check=True).stdout)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    first = ends[0] if starts and starts[0] < 0.05 and ends else 0.0
    # trailing silence: its start is the last speech moment (FFmpeg may or may not print its end at EOF)
    trailing = starts and starts[-1] > first + 0.05 and (len(ends) < len(starts) or ends[-1] >= dur - 0.05)
    last = starts[-1] if trailing else dur
    return first, last, dur

def word_onsets(text, first, last):
    # shortcut: the reading-speed estimate stretched onto the measured speech span, accurate to a few
    # hundred ms; upgrade to forced alignment (e.g. whisper word timestamps) if cues visibly drift.
    est = [x - VO_OFFSET for x in estimate_words(text)]
    span = est[-1] + 0.37
    return [round(first + x / span * (last - first), 3) for x in est]

def main():
    out, problems = {}, []
    for sid, start, dur, vo, text in SCENES:
        path = os.path.join(ROOT, "assets", "voiceover", vo + ".mp3")
        if not os.path.exists(path):
            problems.append(f"missing {vo}.mp3")
            continue
        first, last, clip = speech_span(path)
        if VO_OFFSET + clip > dur - 0.3:
            problems.append(f"{vo}.mp3 is {clip:.1f}s; the scene allows {dur - 0.3 - VO_OFFSET:.1f}s")
        out[vo] = word_onsets(text, first, last)
    json.dump(out, open(os.path.join(ROOT, "build", "vo_words.json"), "w"), indent=1)
    print(f"timed {len(out)} clips")
    if problems:
        print("\n".join(problems))
        sys.exit(1)

if __name__ == "__main__":
    main()
