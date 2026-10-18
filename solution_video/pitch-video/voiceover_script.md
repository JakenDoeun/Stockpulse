# StockPulse pitch film: voice-over script (ElevenLabs production document)

Status: **v2 (visual revision pass).** Lines 02, 03 and 04 are shorter so the product appears at 0:40 (see `revision_notes.md`); the other nine lines are unchanged. Windows below follow the v2 timeline.

- 12 clips, 367 spoken words, inside a 3:23 film. The rest is room for pictures.
- Put the files in `pitch-video/assets/voiceover/` using exactly the filenames below. The build script looks for these names, and a missing file stops the final render. It never skips a clip.
- Numbers are spelled the way they should be spoken ("seven hundred forty-four"). Paste the text exactly as written.

---

## A. Voice design prompt

Formula: `[Audio Quality] + [Gender/Age] + [Accent/Dialect] + [Pacing/Tone] + [Timbre/Persona]`

Paste into **ElevenLabs → Voices → Voice Design**:

```
Studio-quality, close-mic English narration with a clean, dry room and no background noise. Adult male, around 30 to 40 years old. Neutral General American accent. Measured, conversational pacing with natural pauses between ideas; confident but approachable, never salesy or over-excited. Warm, clear mid-low timbre with a little texture, like an informed product storyteller explaining something he built carefully to a smart friend. Not a movie-trailer or commercial announcer voice.
```

Voice Design preview text (it should be over 100 characters; this is chunk 08, which has numbers and a list in it):

```
How much to buy? Deterministic math: demand over the lead time and review period, plus safety stock, minus what's already coming, rounded to full cases. Seven hundred forty-four cans.
```

Generate 3 previews and keep the one that sounds the same on the calm lines (01, 12) and the dense lines (08, 11). Save it as **"StockPulse Narrator"**.

---

## B. Narration, scene by scene

Durations assume about 150 words a minute. Each scene window is longer than its line, so the picture can breathe.

### 01: Hook
- **Scene:** S01 · **Window:** 0:00.5 – 0:14.0 · **Est. spoken:** ~11 s · **Words:** 26
- **File:** `VO_01_HOOK.mp3`
- Performance cue (not spoken): unhurried, almost private. Leave a small pause after each sentence.

```
Every week, a store owner makes the same bet. Order too little, and the shelf runs empty. Order too much, and cash sits in the stockroom.
```

### 02: Problem
- **Scene:** S02 · **Window:** 0:14.5 – 0:29.0 · **Est. spoken:** ~12 s · **Words:** 28
- **File:** `VO_02_PROBLEM.mp3`
- Cue: matter-of-fact. Lean lightly on "scattered."

```
The data already exists, but it's scattered. Sales live in the POS. Supplier changes arrive as PDFs and emails. A three-day delivery delay rarely reaches the reorder sheet.
```

### 03: Why it matters
- **Scene:** S03 · **Window:** 0:29.5 – 0:40.0 · **Est. spoken:** ~8 s · **Words:** 19
- **File:** `VO_03_STAKES.mp3`
- Cue: three short beats, each with equal weight. Don't dramatize.

```
That gap is costly. A stockout sends customers elsewhere. An over-order traps cash. A missed price rise erodes margin.
```

### 04: Introducing StockPulse
- **Scene:** S04 · **Window:** 0:40.5 – 0:50.0 · **Est. spoken:** ~7 s · **Words:** 18
- **File:** `VO_04_INTRO.mp3`
- Cue: a small lift on "StockPulse," then settle. This is the thesis, so say it plainly.

```
StockPulse turns that scattered data into explainable, budget-aware purchasing decisions, without replacing the systems a retailer already uses.
```

### 05: Data intake
- **Scene:** S05 · **Window:** 0:50.5 – 1:09.0 · **Est. spoken:** ~16 s · **Words:** 40
- **File:** `VO_05_INTAKE.mp3`
- Cue: "Take one decision" starts the walkthrough, so slow down a little. Say "five days to eight" cleanly.

```
Take one decision. Angkor Beverage sends revised terms: delivery goes from five days to eight, and the cost of Cola rises eight cents a can. StockPulse turns the document into structured fields, and nothing changes until a person confirms them.
```

### 06: Demand forecasting
- **Scene:** S06 · **Window:** 1:09.5 – 1:28.0 · **Est. spoken:** ~13 s · **Words:** 31
- **File:** `VO_06_FORECAST.mp3`
- Cue: say "not a language model" as a quiet aside, not a jab.

```
Next, demand. Dedicated time-series models, not a language model, forecast each product. Cola should sell about eight hundred sixty units over the next two weeks, scored against a simple moving-average baseline.
```

### 07: Risk detection
- **Scene:** S07 · **Window:** 1:28.5 – 1:46.0 · **Est. spoken:** ~14 s · **Words:** 35
- **File:** `VO_07_RISK.mp3`
- Cue: the turn of the story. A little more weight on "no longer lasts" and "critical", but keep the tone level.

```
Now the consequence. At eight days, the stock on hand and on order no longer lasts. Fixed rules flag Cola as critical: it runs out more than two days before a new delivery can arrive.
```

### 08: Replenishment and budget trade-offs
- **Scene:** S08 · **Window:** 1:46.5 – 2:09.0 · **Est. spoken:** ~20 s · **Words:** 48
- **File:** `VO_08_OPTIMIZE.mp3`
- Cue: read the formula like a sentence, not a list. Pause briefly before "Seven hundred forty-four cans."

```
How much to buy? Deterministic math: demand over the lead time and review period, plus safety stock, minus what's already coming, rounded to full cases. Seven hundred forty-four cans. Cut the budget by thirty percent, and critical items stay covered while lower-priority lines give up safety stock first.
```

### 09: Procurement agent and human approval
- **Scene:** S09 · **Window:** 2:09.5 – 2:26.0 · **Est. spoken:** ~14 s · **Words:** 33
- **File:** `VO_09_AGENT.mp3`
- Cue: "It explains the numbers; it never invents them" is the trust line, so say it calmly and with conviction. Slow down on the last sentence.

```
The procurement agent explains the trade-off in plain English and prepares a purchase order draft. It explains the numbers; it never invents them. And it can't approve. A person reviews and signs off.
```

### 10: Core features and target users
- **Scene:** S10 · **Window:** 2:26.5 – 2:46.0 · **Est. spoken:** ~14 s · **Words:** 35
- **File:** `VO_10_FEATURES.mp3`
- Cue: an even rhythm through the list. Turn warmer on "Built for."

```
One connected workflow: supplier and sales intake, transparent forecasting, risk detection, constraint-aware replenishment, and an agent that explains its work. Built for independent retailers, specialty grocers, and small wholesalers already running a POS or spreadsheet.
```

### 11: Architecture and AMD infrastructure
- **Scene:** S11 · **Window:** 2:46.5 – 3:09.0 · **Est. spoken:** ~17 s · **Words:** 40
- **File:** `VO_11_TECH.mp3`
- Cue: precise, a touch slower. Say "AMD Instinct" and "ROCm" (spoken "rock-em") clearly; if ROCm is mispronounced, see C.4.

```
Under the hood, the line is strict. Forecasts, risk rules, and quantities are deterministic, auditable code. Language models on AMD Developer Cloud, with AMD Instinct GPUs and ROCm, read documents and explain results, so pricing and margin data stays private.
```

### 12: Closing
- **Scene:** S12 · **Window:** 3:09.5 – 3:23.0 · **Est. spoken:** ~6 s · **Words:** 14
- **File:** `VO_12_CLOSE.mp3`
- Cue: three settled beats, then the name. Leave a full beat of silence before "StockPulse."

```
Fewer empty shelves. Less cash stuck on the floor. Decisions you can explain. StockPulse.
```

---

## C. ElevenLabs generation instructions

1. **Model: Eleven Multilingual v2.** It's the most consistent ElevenLabs model for long-form narration, and consistency across 12 separate clips matters more here than expressiveness. Eleven v3 is more expressive but varies more from take to take, so use it only if v2 sounds flat, and then use it for all 12 clips.
2. **Voice settings** (Text to Speech → settings). Use the same values for every clip:
   - Stability **0.50**. Lower sounds livelier but drifts between clips; higher sounds robotic.
   - Similarity **0.75**
   - Style exaggeration **0.10**. Keep it low: higher values push toward an announcer voice and add artifacts.
   - Speaker boost **on**
   - Speed **1.00**. Don't speed clips up to fit; the timeline is built to fit the speech.
3. **Output format: MP3 44.1 kHz 192 kbps** (or WAV / PCM 44.1 kHz if your plan allows it). The mix step resamples everything to 48 kHz stereo.
4. **Pronunciation.** If "ROCm" comes out as letters, re-generate that clip with `ROCm` spelled `Rock-em`, but only in that clip. "POS" should be said as letters ("P-O-S"); if it comes out as "pos", use `P.O.S.`.
5. **Consistency.** Generate all 12 clips in one session with the same voice and settings. If one clip sounds different (pitch, energy), regenerate that clip only. Don't change the settings mid-batch.
6. **Trimming.** Leave about 0.1–0.3 s of natural room tone at the start and end. Don't hard-trim breaths or add fades; the build script handles the clip edges.
7. **Placement.** Save to `pitch-video/assets/voiceover/VO_NN_NAME.mp3` with exactly these names:

| # | File | Scene start in film |
|---|---|---|
| 01 | `VO_01_HOOK.mp3` | 0:00.5 |
| 02 | `VO_02_PROBLEM.mp3` | 0:14.5 |
| 03 | `VO_03_STAKES.mp3` | 0:29.5 |
| 04 | `VO_04_INTRO.mp3` | 0:40.5 |
| 05 | `VO_05_INTAKE.mp3` | 0:50.5 |
| 06 | `VO_06_FORECAST.mp3` | 1:09.5 |
| 07 | `VO_07_RISK.mp3` | 1:28.5 |
| 08 | `VO_08_OPTIMIZE.mp3` | 1:46.5 |
| 09 | `VO_09_AGENT.mp3` | 2:09.5 |
| 10 | `VO_10_FEATURES.mp3` | 2:26.5 |
| 11 | `VO_11_TECH.mp3` | 2:46.5 |
| 12 | `VO_12_CLOSE.mp3` | 3:09.5 |

Each clip starts 0.3 s after its scene's start. If a real clip runs longer than its window, the build reports it. The fix is to tighten that scene's text or retime the scene, never to time-stretch the speech.
