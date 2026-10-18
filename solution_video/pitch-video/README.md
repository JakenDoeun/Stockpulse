# StockPulse pitch film

3:23 product pitch film (v2) · 1920×1080 · native 60 fps · H.264 + AAC 48 kHz stereo · subtitles burned into the final, `captions.srt` sidecar.

v2 is a visual revision pass: see `revision_notes.md`. The v1 sources are kept in `versions/v1/`, and the v1 preview stays at `build/stockpulse_pitch_PREVIEW.mp4`.

Planning documents: `revision_notes.md` (v2) · `storyboard.md` (scenes and shot list) · `voiceover_script.md` (ElevenLabs) · `claim_audit.md` · `asset_manifest.md` · `audio_cue_sheet.md` · `frame.md` (design spec) · `boards/storyboard.html` (sketch board).

## Requirements

Node 18+ (`npx hyperframes`, pinned in `package.json`), Python 3 with numpy, FFmpeg with libass. Recapturing app footage also needs the app's venv and Playwright (`../../node_modules`).

## Final video (after the voice-over is recorded)

1. Generate the 12 clips described in `voiceover_script.md` and save them as `assets/voiceover/VO_01_HOOK.mp3` … `VO_12_CLOSE.mp3`.
2. Run:

```bash
bash scripts/final.sh
```

This measures each clip, re-times every animation cue and caption to the real speech (`scripts/vo_timing.py`), regenerates the scenes, re-renders the picture at 60 fps, then mixes, ducks the music under the voice, normalizes loudness (−16 LUFS, −1.5 dBTP), burns the captions and encodes `build/stockpulse_pitch_FINAL.mp4`. `build/verify.json` records the ffprobe and loudness checks. The build stops if any clip is missing or runs longer than its scene.

## Picture-lock preview (no voice-over)

```bash
python3 scripts/gen_frames.py          # scenes, timed to a reading-speed estimate
npx hyperframes render --fps 60 --quality delivery --workers 4 --strict -o build/picture.mp4
python3 scripts/build.py               # → build/ui_sfx_stem.wav + build/stockpulse_pitch_v2_SFX_PREVIEW.mp4 (picture + UI cues only; captions.srt sidecar)
```

## Editing

- **Camera rule:** every browser has one `.cam` parent that is the only moving part (`camv()` / `camTo` in `gen_frames.py`): one move, then a hold. Never animate the frame, the images and the camera at once.
- **Scenes** (`compositions/frames/s01…s12-*.html`) are generated. Edit `scripts/gen_frames.py`, then rerun it. Motion cues are keyed to words in the narration, so a script change moves its animation with it.
- **Shared look:** `assets/film.css` (tokens from the app's `tokens.css`). **Timeline:** `index.html`.
- **Studio preview:** `npx hyperframes preview --background` (stop it with `--stop`). **Checks:** `npx hyperframes check` and `python3 scripts/selftest.py`.
- **UI sound effects:** `python3 scripts/make_sfx.py` (original, deterministic; same cues as the app). Placement and outputs: `audio_cue_sheet.md`. `build.py` writes the cue layer as `build/ui_sfx_stem.wav`. Music (`make_audio.py`) and voice-over are separate layers.
- **App captures:** start a throwaway engine from the app root (`DB_PATH=/tmp/capture.db .venv/bin/python -m uvicorn app.main:app --port 8811`), then `NODE_PATH=../../node_modules node capture/capture_v2.cjs` from here (writes `capture/v2/` at 2× device scale with animations and the caret disabled). Use a fresh `DB_PATH` each time, or the PO number and the verified-state history drift. It asserts the Cola numbers (744 × $1.36 = $1,011.84) before writing stills.
