"""Assembles the deliverable from the rendered picture, the audio assets and the captions.

    python3 scripts/build.py            # final if all 12 VO clips exist, otherwise a picture-lock preview

Inputs:  build/picture.mp4 (HyperFrames render, 60 fps), build/cues.json (from gen_frames.py),
         assets/audio/ui_*.wav (UI cues, make_sfx.py), assets/audio/music_bed.wav, assets/voiceover/VO_*.mp3 (ElevenLabs).
Outputs: build/ui_sfx_stem.wav (the UI cue layer alone, film length, never mixed into music or voice),
         captions.srt, build/captions.ass, build/stockpulse_pitch_v2_SFX_PREVIEW.mp4 (picture + UI cues only)
         or build/stockpulse_pitch_FINAL.mp4, build/loudness.json, build/verify.json
"""
import json, os, re, subprocess, sys
from gen_frames import VO_OFFSET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = lambda *p: os.path.join(ROOT, *p)
MAX_RUNTIME = 225.0
MIN_GAP = 0.4  # seconds between UI cues: they never stack

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)

def probe_dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout)

# ---------------------------------------------------------------- captions
def ts(t, sep):
    h, r = divmod(max(t, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", sep) if sep == "," else f"{int(h)}:{int(m):02d}:{s:05.2f}"

def wrap(words, width=46):
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur]

def caption_cues(cues):
    out = []
    for sc in cues.values():
        words, chunk = sc["words"], []
        for i, (w, t) in enumerate(words):
            if chunk and len(wrap([x for x, _ in chunk] + [w])) > 2:  # never more than two lines
                out.append((chunk[0][1], t - 0.05, wrap([x for x, _ in chunk]))); chunk = []
            chunk.append((w, t))
            text = " ".join(x for x, _ in chunk)
            last = i == len(words) - 1
            if w[-1] in ".?;:" or (w[-1] == "," and len(text) > 28) or last:
                end = words[i + 1][1] - 0.05 if not last else min(t + 0.6, sc["start"] + sc["duration"] - 0.4)
                out.append((chunk[0][1], end, wrap([x for x, _ in chunk])))
                chunk = []
    # merge very short cues into the next one in the same breath
    merged = []
    for c in out:
        if merged and merged[-1][1] - merged[-1][0] < 1.0 and c[0] - merged[-1][1] < 0.2 and len(merged[-1][2]) + len(c[2]) <= 2:
            p = merged.pop(); c = (p[0], c[1], wrap(" ".join(p[2] + c[2]).split()))
        merged.append(c)
    return merged

def write_captions(cues):
    caps = caption_cues(cues)
    with open(B("captions.srt"), "w") as f:
        for i, (a, b, lines) in enumerate(caps, 1):
            f.write(f"{i}\n{ts(a, ',')} --> {ts(b, ',')}\n" + "\n".join(lines) + "\n\n")
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Geist Medium,40,&H003B2A20,&H003B2A20,&H10FFFFFF,&H10FFFFFF,0,0,0,0,100,100,0,0,4,14,0,2,200,200,46,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(B("build", "captions.ass"), "w") as f:
        f.write(head)
        for a, b, lines in caps:
            f.write(f"Dialogue: 0,{ts(a, '.')},{ts(b, '.')},Cap,,0,0,0,," + r"\N".join(lines) + "\n")
    return len(caps)

# ---------------------------------------------------------------- audio graph
def write_stem(cues, TOTAL):
    """The UI cue layer as its own track. Cues are pre-levelled in make_sfx.py, so they go in at unity gain."""
    hits = sorted((t, name) for sc in cues.values() for name, t in sc["sfx"])
    for (a, n1), (b, n2) in zip(hits, hits[1:]):
        assert b - a >= MIN_GAP, f"UI cues {n1}@{a:.2f}s and {n2}@{b:.2f}s would stack"
    ins = sum([["-i", B("assets", "audio", f"ui_{name}.wav")] for _, name in hits], [])
    parts = [f"[{i}:a]adelay={int(t * 1000)}|{int(t * 1000)}[s{i}]" for i, (t, _) in enumerate(hits)]
    parts.append("".join(f"[s{i}]" for i in range(len(hits))) + f"amix=inputs={len(hits)}:normalize=0,apad,atrim=0:{TOTAL}[out]")
    run(["ffmpeg", "-hide_banner", "-y", *ins, "-filter_complex", ";".join(parts), "-map", "[out]",
         "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", B("build", "ui_sfx_stem.wav")])
    return B("build", "ui_sfx_stem.wav"), hits

def audio_graph(cues, vo_files, TOTAL, stem):
    if not vo_files:  # preview: the UI cue layer alone; music and voice are mixed elsewhere
        return [stem], f"[1:a]apad,atrim=0:{TOTAL}[mix]"
    inputs, parts, vo_labels = [B("assets", "audio", "music_bed.wav"), stem], [], []
    for sc in cues.values():
        if sc["vo"] in vo_files:
            inputs.append(vo_files[sc["vo"]]); k = len(inputs)
            ms = int((sc["start"] + VO_OFFSET) * 1000)
            parts.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=mono,pan=stereo|c0=c0|c1=c0,adelay={ms}|{ms}[v{k}]"); vo_labels.append(f"[v{k}]")
    parts.append(f"{''.join(vo_labels)}amix=inputs={len(vo_labels)}:normalize=0,asplit[vo][key]")
    parts.append("[1:a]volume=0.22[mus]")
    parts.append("[mus][key]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400:makeup=1[bed]")
    parts.append("[bed][2:a][vo]amix=inputs=3:normalize=0,apad,atrim=0:" + str(TOTAL) + "[mix]")
    # input 0 is the picture; audio inputs start at 1 (music, UI cue stem, then the voice clips)
    return inputs, ";".join(parts)

def main():
    cues = json.load(open(B("build", "cues.json")))
    TOTAL = max(sc["start"] + sc["duration"] for sc in cues.values())
    if not os.path.exists(B("build", "picture.mp4")):
        sys.exit("build/picture.mp4 missing: render first (see README).")
    vo_dir = B("assets", "voiceover")
    vo_files = {sc["vo"]: os.path.join(vo_dir, sc["vo"] + ".mp3") for sc in cues.values() if os.path.exists(os.path.join(vo_dir, sc["vo"] + ".mp3"))}
    missing = [sc["vo"] + ".mp3" for sc in cues.values() if sc["vo"] not in vo_files]
    final = not missing
    if missing and len(missing) < len(cues):
        print("Some voice-over clips are present but these are missing, so building a PREVIEW only:\n  " + "\n  ".join(missing))
    if final:
        timing = B("build", "vo_words.json")
        if not os.path.exists(timing):
            sys.exit("All clips present, but the picture is still timed to estimates. Run scripts/final.sh (it re-times, re-renders, then builds).")
        for sc in cues.values():  # never let a clip run past its scene
            d = probe_dur(vo_files[sc["vo"]])
            if sc["start"] + VO_OFFSET + d > sc["start"] + sc["duration"] - 0.3:
                sys.exit(f"{sc['vo']}.mp3 is {d:.1f}s, longer than its scene window; tighten the line or retime the scene.")

    n_caps = write_captions(cues)
    stem, hits = write_stem(cues, TOTAL)
    audio_inputs, graph = audio_graph(cues, vo_files if final else {}, TOTAL, stem)
    out = B("build", "stockpulse_pitch_FINAL.mp4" if final else "stockpulse_pitch_v2_SFX_PREVIEW.mp4")
    ins = sum([["-i", p] for p in audio_inputs], [])

    meas, ln = {}, "anull"  # the UI-cue preview keeps the stem's own level; a loudness-normalised cue layer would be far too loud
    if final:  # pass 1: measure loudness of the full mix
        m = run(["ffmpeg", "-hide_banner", "-nostats", "-i", B("build", "picture.mp4"), *ins, "-filter_complex",
                 graph + ";[mix]loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json[out]", "-map", "[out]", "-f", "null", "-"]).stderr
        meas = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
        ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:"
              f"measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true")

    # Subtitles are burned only over real narration, in one lower-third style. The voice-over-ready preview carries
    # no burned text and no label (captions.srt is the sidecar); the file name says what it is.
    vf = (f"[0:v]subtitles={B('build', 'captions.ass')}:fontsdir={B('assets', 'fonts')}[v]" if final else "[0:v]null[v]")
    run(["ffmpeg", "-hide_banner", "-y", "-i", B("build", "picture.mp4"), *ins, "-filter_complex",
         graph + f";[mix]{ln},aresample=48000[a];{vf}", "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", "120",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-t", str(TOTAL), out])

    # verify
    v = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels:format=duration",
                        "-of", "json", out]).stdout)
    post = run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr
    post = json.loads(post[post.rindex("{"):post.rindex("}") + 1])
    vs = next(s for s in v["streams"] if s["codec_name"] == "h264"); au = next(s for s in v["streams"] if s["codec_name"] == "aac")
    report = {"output": out, "mode": "FINAL" if final else "UI SFX PREVIEW", "ui_sfx_stem": stem, "ui_cues": [[round(t, 2), n] for t, n in hits],
              "missing_voiceover": missing, "captions": n_caps,
              "video": vs, "audio": au, "duration": float(v["format"]["duration"]),
              "loudness": {"integrated_lufs": post["input_i"], "true_peak_dbtp": post["input_tp"], "lra": post["input_lra"]}}
    assert vs["r_frame_rate"] == "60/1" and vs["avg_frame_rate"] == "60/1", vs
    assert (vs["width"], vs["height"]) == (1920, 1080)
    assert au["sample_rate"] == "48000" and au["channels"] == 2
    assert report["duration"] <= MAX_RUNTIME
    json.dump(report, open(B("build", "verify.json"), "w"), indent=1)
    json.dump(meas, open(B("build", "loudness.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))
    if missing:
        print("\nPREVIEW ONLY. Missing voice-over clips (put them in assets/voiceover/):\n  " + "\n  ".join(missing)
              + "\nThen run: bash scripts/final.sh")

if __name__ == "__main__":
    main()
