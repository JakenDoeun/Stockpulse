# Audio cue sheet: UI sound effects

**Scope.** This file covers the UI sound-effect layer only. Background music and voice-over are handled separately and are not generated, edited or mixed by this layer.

## What changed (UI SFX redesign)

- **Removed:** the seven v1/v2 effects (`sfx_paper`, `sfx_data`, `sfx_rise`, `sfx_alert`, `sfx_swish`, `sfx_confirm`, `sfx_tick`).
  - They were deleted from `assets/audio/`, and `scripts/make_audio.py` no longer generates them; copies remain in `versions/v1/assets/audio/`.
  - Most of them sat on decorative motion (logo reveals, swishes, chart draws, the illustration's alert) rather than on interface events.
- **Added:** five cues from `scripts/make_sfx.py`, using the same notes and envelopes as the app's own cues (`frontend/src/lib/sfx.ts`), so the film sounds like the product:

| Cue | Sound | Length (audible) | Used for |
|---|---|---|---|
| `ui_tap` | one soft 1.2 kHz tick, film only | ~0.05 s | a visible cursor press on a real control |
| `ui_select` | two quick rising notes, A5 → E6 | ~0.3 s | a document received |
| `ui_review` | two even notes, D5 | ~0.4 s | values or a risk that need a person's attention |
| `ui_success` | gentle E–G♯–B chime | ~0.6 s | an outcome confirmed by the app (verified, approved) |
| `ui_error` | two falling notes, C5 → G4 | ~0.5 s | a failure (in the set for parity with the app; the film shows none) |

## Levels

- Each cue is a sine voice plus a quiet octave, with a 4 ms attack and an exponential decay; there is no reverb and no layering.
- The cues are balanced by measured K-weighted loudness (max momentary): select, review, success and error sit within about 1 dB of each other, and tap sits about 13 dB below them.
- The loudest cue peaks at −12 dBFS.

## Placement

Cues sit only on visible UI events, never on titles, transitions or illustrations. They are at least 0.4 s apart (`build.py` refuses a stacked pair). Times come from `build/cues.json` and move with the narration when `scripts/final.sh` re-times the film.

| Time | Scene | Cue | Visible event |
|---|---|---|---|
| 0:21.24 | s02-problem | `ui_select.wav` | The "New" badge lands on the Angkor PDF |
| 0:52.09 | s05-intake | `ui_select.wav` | The supplier PDF arrives next to the real Supplier Inbox |
| 1:01.78 | s05-intake | `ui_review.wav` | The first extracted field lands on the real review form (values to review) |
| 1:06.10 | s05-intake | `ui_tap.wav` | The cursor presses Confirm |
| 1:06.60 | s05-intake | `ui_success.wav` | The page turns Verified |
| 1:37.02 | s07-risk | `ui_review.wav` | The real Risk Radar row is ringed as Critical |
| 1:59.91 | s08-optimize | `ui_tap.wav` | The cursor presses −30% in the real what-if simulator |
| 2:21.79 | s09-agent | `ui_tap.wav` | The cursor presses Approve |
| 2:23.24 | s09-agent | `ui_success.wav` | The purchase order turns Approved |

Nine cues across the 3:23 film. Deliberately silent:
- the opening illustration (S01–S04);
- the forecast chart (S06);
- the equation (S08 part A);
- the workflow and architecture diagrams (S10–S11);
- the close (S12);
- the second (Confirm) click in S09, which would stack on the Approved chime.

## Outputs

- **`build/ui_sfx_stem.wav`**
  - The UI cue layer alone: 48 kHz stereo, 16-bit, the film's full length, cues at their film times.
  - It is not loudness-normalised; mix it under music and voice yourself.
- **`build/stockpulse_pitch_v2_SFX_PREVIEW.mp4`**
  - The v2 picture with only the UI cue stem as audio, for checking sync.
  - The earlier `stockpulse_pitch_v2_PREVIEW.mp4` still contains the old effects and the music bed. It is kept for reference only.
- **`build.py` final mode** (all 12 VO clips present) is unchanged apart from this layer: it still mixes the existing music bed, the VO and this stem. If you mix music and voice elsewhere, use the stem.

Rebuild with:

```bash
python3 scripts/make_sfx.py
python3 scripts/gen_frames.py
python3 scripts/build.py
```

The picture doesn't need re-rendering for an SFX-only change.
