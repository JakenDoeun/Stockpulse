# Revision notes: v2 visual pass

The source is `build/stockpulse_pitch_PREVIEW.mp4`, the v1 picture-lock: 3:42, no voice-over. I reviewed it frame by frame. For the opening that meant contact sheets every 2–4 s from 0:00 to 1:06. For the browser scenes I measured motion with a per-frame phase-correlation script (sub-pixel x/y shift between consecutive 60 fps frames).

**Rollback.** The v1 sources are in `versions/v1/` (scripts, compositions, CSS, audio, captions, VO script, storyboard, `picture.mp4`). The v1 film stays at `build/stockpulse_pitch_PREVIEW.mp4` and the v1 stills at `capture/prod/`. Nothing in v1 is overwritten. v2 writes `build/stockpulse_pitch_v2_PREVIEW.mp4`.

## 1. Weak scenes (v1 timecodes)

| v1 time | Scene | Problem |
|---|---|---|
| 0:00–0:15 | S01 hook | A thin balance-scale line drawing sits in the middle third. Its tilt is ±5°, which barely registers. The headline "Every week, the same bet." stays on screen for all 15 s, and roughly 60% of the frame is empty. |
| 0:15–0:38 | S02 problem | Four document cards fade in and drift ±6 px for 9 s. Nothing happens to them, and the "5 days → 8 days" chip floats with no cause and effect. The reorder sheet is a small dashed box. |
| 0:38–0:55 | S03 stakes | A three-column text grid with 96 px line icons. The numbers count up, but nothing links them to the story. |
| 0:55–1:10 | S04 intro | The product appears only at 0:55. The logo, tagline and subline sit on an empty canvas for 9 s, then the dashboard shows at 0.98× with 12–13 px UI text and scrolls 420 px. |
| every scene | Captions | A white caption box with the full narration sits at the bottom of every frame. Without a voice it reads as a repeated explanatory sentence. |
| every scene | Label | "PREVIEW · NO VOICE-OVER" is burned into the top-right of the picture. |
| 1:10–1:28 | S05 intake | The review form changes between three stills with different crops and scales (0.79× at y 255, then 0.66× at y 200, then 0.79× at y 90). Every state change reframes the page, which reads as a jump. The UI text is 11–13 px. |
| 1:28–1:47 | S06 forecast | The whole screenshot zooms 3.5% over 18 s, and a white cover wipes the chart. The forecast line is never drawn, only uncovered. |
| 1:47–2:05 | S07 risk | The concept is sound, but the risk row is a 196 px strip with 13 px text and a mono rule box. |
| 2:05–2:28 | S08 optimize | The budget what-if happens inside a 0.99× screenshot. The figures below it are text with no visual cause: nothing shows the budget line moving or the lines shrinking. |
| 2:45–3:05 | S10 features | The five workflow thumbnails are at 0.3×, so each is unreadable. |
| 3:05–3:28 | S11 architecture | Eleven boxes and five arrows with 15–18 px descriptions, too dense to read at speaking pace. |
| 3:28–3:42 | S12 close | The balance scale comes back as a bare line. |

## 2. Source of the UI jitter

Phase correlation on the rendered v1 picture (`build/picture.mp4`, archived to `versions/v1/`) points to four sources:

1. **Whole-pixel snapping on non-composited transforms.**
   - The `rise` entrances (y 30 → 0 with `power3.out`) should slow down smoothly. Instead the per-frame speed moves in steps of −1.99, −1.97, −1.81, −1.97, −1.10, −1.31 px/frame (S08 at 2:08, S07 at 1:54).
   - The S04 scroll has the same ±0.3 px/frame unevenness.
   - GSAP's `force3D: "auto"` composites the element during a tween and hands it back to the main painter afterward, so positions round to whole pixels and the image re-rasterizes at the end of every move.
   - **Cause:** the animation, not the source recordings.
2. **State changes reframe the page.** In S05, the three review states were captured at different scroll positions and placed at different crops and scales (above). Each crossfade is therefore also a 50–165 px reframe.
   - **Cause:** both the captures and the composition.
3. **Slow sub-pixel creep on text.**
   - S06 scales by 1.000 → 1.035 over 18 s, about 0.003 px of change per frame.
   - S02 drifts its cards ±6 px over 9 s.
   - S04 nests the frame's own scale (0.94 → 1) and y-rise inside the camera scroll.
   - Each frame resamples the text slightly differently, which reads as crawl or shimmer rather than as motion.
4. **Soft source pixels.** The stills were 1600 × 900 CSS px at 1.2× device scale (1920 px wide) and were shown at 0.66–1.15×. That is non-integer resampling of 13 px UI text, with no animations disabled during capture.

## 3. Planned corrections

### Timing
The product moves earlier. S01–S04 shrink from 70 s to 50 s, the film runs 3:22 (202 s), and the scenes after S04 keep their length.

| Scene | v1 | v2 | Window |
|---|---|---|---|
| S01 hook | 0:00 / 15 s | 0:00 / 15 s | Hook 0:00–0:06, trade-off 0:06–0:15 |
| S02 problem | 0:15 / 23 s | 0:15 / 14 s | Scattered POS and supplier data, 0:15–0:29 |
| S03 stakes | 0:38 / 17 s | 0:29 / 11 s | Consequences, 0:29–0:40 |
| S04 intro | 0:55 / 15 s | 0:40 / 10 s | Logo and real dashboard, 0:40–0:50 |
| S05–S12 | 1:10 → 3:42 | 0:50 → 3:22 | Product story, same lengths |

Three lines are shortened, VO_02, VO_03 and VO_04, so they fit the new windows. `voiceover_script.md` is updated.

### Opening (S01–S04): one connected vector story
- The illustrations are solid geometric shapes with two or three tonal layers each: shelf boards with a front lip, cans and bottles with label bands, cartons with a top and side face. They use the light canvas, deep ink, indigo and blue, with red-coral only for the problem states.
- **S01:** a stocked shelf (24 facings) and a stockroom are built in the first second.
  - An order slip's slider swings: that is the bet.
  - On "too little", 15 facings sell off and leave dashed gaps, and an "Empty shelf" tag appears.
  - On "too much", 14 cartons drop into the stockroom one at a time and a "Cash tied up" badge locks onto the stack.
- **S02:** it starts on S01's last frame, so the cut is seamless.
  - The shelf turns into the POS terminal (sales come from the shelf), the stockroom into the supplier documents, and the order slip into the stale reorder sheet.
  - The connector paths draw but stop short of the sheet.
  - The delivery truck marker moves from day 5 to day 8.
  - A "+3 days" token heads for the sheet and never arrives, so the sheet keeps "5 d".
- **S03:** the delivery timeline carries over and becomes the stockout panel: coverage runs out 2.3 days before the truck.
  - The carton stack becomes trapped capital.
  - A unit-cost tag flips from $1.28 to $1.36, and the same move shrinks the margin bar from $1.22 to $1.14.
- **S04:** three data chips draw along curved paths into the StockPulse logo. The real dashboard then rises at a wide, readable framing, makes one camera move to the KPI row, and holds.

### Motion and camera rules (all scenes)
- Each browser has a single camera parent (`.cam`) that is the only thing moved. It is composited for the whole scene (`will-change: transform`, `force3D: true`), so nothing switches between composited and non-composited mid-scene.
- The image is laid out at the closest framing the scene needs, so camera scale is always ≤ 1. Zooming out is a GPU downsample and never enlarges a raster.
- Every move is one scale-and-position tween with `power2.inOut`, followed by a complete hold. There are no slow drifts or ambient zooms, and no reframing on a state change.
- States that dissolve into each other use pixel-aligned captures at the same scroll position, so only the changed UI changes.
- Browser frames enter with opacity and a short slide on the outer wrapper before any camera move, never during one.

### Captures (re-recorded)
`capture/capture_v2.cjs` writes to `capture/v2/`:
- 1600 × 900 CSS at **2× device scale** (3200 px wide);
- `reducedMotion: reduce`, with all transitions, animations and the caret disabled;
- `animations: "disabled"`, `caret: "hide"`, and the mouse parked outside the UI;
- the review states saved as full pages from scroll 0, so all three align (verified: the first differing row between "review" and "ready" is the edited row itself);
- the same app asserts as before (Cola 744 × $1.36 = $1,011.84, lead time 8);
- a fresh throwaway database, which gives PO-00001 and no leftover history.

### Text, captions and labels
- The bottom caption box is removed from the preview. `captions.srt` is still written as a sidecar file.
- The final burns subtitles timed to the real voice, in one lower-third style.
- The scenes use short 3–6 word callouts in place of sentence text.
- The "PREVIEW · NO VOICE-OVER" overlay is removed. The preview is identified by its file name only.
- The Calculated/AI legend stays only where blue and ember both appear (S05, S06, S11). It moves to the top-right and is larger.

### Product and technical scenes
- **S05:**
  - one framing of the real review form at 1.12× CSS, where text is 15–17 px;
  - ember field chips fly from the PDF lines and land on the matching real fields (lead time 8, unit cost 1.36, MOQ 48, case pack 24);
  - one camera move down to the excluded lines and the Confirm button, then the human click;
  - the page then changes to the verified state.
- **S06:** a chart redrawn from the engine's own forecast API (`capture/v2/forecast_SKU008.json`).
  - The 56 days of actual Cola sales draw in, then the 14-day forecast, then the 80% interval band.
  - The SMA-14 baseline is a dashed line.
  - The WAPE comparison is 28.8% vs 31.8%.
  - A crop of the real forecast page confirms the numbers: 861 units, 754–968, SMA-14 879.
- **S07:** stock coverage (5.7 days) against the truck marker, which moves from day 5 to day 8, with the 2.3-day gap in red. The fixed rule appears as one readable line, followed by the real Risk Radar row at 1.2×.
- **S08:**
  - the equation tiles stay;
  - the budget becomes a bar: the limit marker moves from $12,000 to $8,400, plan spend re-solves from $9,714.28 to $8,355.02, the 5 of 5 critical lines stay solid, and Dish Soap (260 → 190) and Body Lotion (318 → 132) shrink;
  - next to it is the real what-if panel at the same framing before and after the −30% click.
- **S09:** the same crop for every approval state; the cursor fades sooner.
- **S10:** vector icon nodes in place of the 0.3× thumbnails; the same labels and users.
- **S11:** three columns:
  - Operational data;
  - Intelligence & optimization, with deterministic code in blue and the AI services on AMD Developer Cloud in coral;
  - Procurement decisions: PO draft, then human approval.

  It uses a few 24–28 px labels. The disclosure line stays.
- **S12:** a callback to the opening. The shelf refills, the stockroom clears, then the logo.

## 4. Data consistency audit

The film uses one scenario: SKU008 Cola 330ml, Angkor Beverage Co, on the sample store's data. I checked every on-screen value against `app/data_sample/*.csv`, the fixture `doc-angkor-pl` (`frontend/src/data/demo.ts`), the engine API, or the new captures.

| Value | Where | Source | Status |
|---|---|---|---|
| Lead time 5 → 8 days; unit cost $1.28 → $1.36 (+6.3%) | S02, S03, S05, S07, S09 | Fixture plus suppliers.csv (S2 = 5 d) and the verified-state capture | ✔ |
| Sales 71 / 32 / 26 (Oct 13–15) | S02 POS receipt | `sales.csv` | ✔ |
| Margin per can $1.22 → $1.14 | S03 | Price $2.50 minus cost ($1.28 / $1.36) | ✔ |
| $42,775 stock beyond 90 days of cover | S03 | Overview before the update (sample store) | ✔, labelled as sample store |
| "4 products" at stockout | S03 (v1) | Overview *before* the update; Risk Radar shows 5 Critical *after* it | ⚠ **Removed.** It conflicted with the post-update state. S03's stockout panel now uses Cola's own 2.3-day gap, the figure S07 also uses. |
| 861 units / 14 d; 80% range 754–968; SMA-14 879; WAPE 28.8% vs 31.8% | S06 | Forecast API: the 14-day sum is 861; `sma14` × 14 = 879; holdout WAPE 0.2876 / 0.3175 | ✔ |
| 5.7 days of supply; 110 + 240 on order; 61.3 a day; 2.3 days short; $161 | S07 | Risk Radar capture | ✔ |
| 486 + 429 + 174 − 350 = 740 → 744; $1,011.84 | S08, S09 | Cart "Why this quantity?" and the PO capture (asserted) | ✔ |
| $12,000 → $8,400; $9,714.28 → $8,355.02; 5 of 5; Dish Soap 260 → 190; Body Lotion 318 → 132 | S08 | What-if captures | ✔ |
| PO-00001 | S09 | v2 capture (fresh database) | ✔. The first v2 attempt reused a stale database and showed PO-00006, so it was recaptured. |
| "100 to 10,000+ SKUs" | S10 | Project proposal, "Primary Market" | ✔ (positioning, not a customer claim) |

## 5. Remaining limits (stated honestly)

- **No voice-over yet.** Cue timing comes from a reading-speed estimate until the ElevenLabs clips arrive; `scripts/final.sh` then re-times everything. VO_03 (S03, 11 s) and VO_04 (S04, 10 s) have under 2 s of slack. If a clip comes back slow, `vo_timing.py` stops the build and names it.
- **The audio is unheard.** I can measure the music and effects but not listen to them; the user should audition the mix.
