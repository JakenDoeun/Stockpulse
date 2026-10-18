---
format: 1920x1080
fps: 60
duration: 203s
message: "StockPulse turns disconnected operational data into explainable, budget-aware purchasing decisions without requiring retailers to replace their existing systems."
arc: Hook → Problem → Stakes → Promise → Intake → Forecast → Risk → Optimize → Agent + Human → Features/Users → Architecture → Close
audience: Hackathon judges (AMD Track 3) first; independent retailers, specialty grocers and small wholesalers second
mode: collaborative
---

# StockPulse pitch film: storyboard (plan pass, awaiting approval)

> **v2 revision.** This file is the approved v1 plan. The visual revision pass changed it: the opening (S01–S04) is now one connected vector story ending at 0:50, the browser scenes use a single steady camera, and S06, S08, S10, S11 and S12 were redrawn. `revision_notes.md` is authoritative for v2 timings and visuals, and `scripts/gen_frames.py` is the source. The scene intent, claims and narration rules below still apply.

## Creative concept

**"One can of Cola."** The whole film follows a single real purchasing decision from the demo dataset, from start to finish: **Cola 330ml (SKU008)** at the demo store *Phnom Penh Central*, supplied by **Angkor Beverage Co**. One supplier PDF changes two numbers: lead time goes from **5 to 8 days** and unit cost from **$1.28 to $1.36**. That single change carries the story: the forecast shows what will sell, the risk rules show the shelf going empty, the optimizer sizes the order inside the budget, the agent explains it, and a person approves. Every product number on screen comes from the running app or its sample data.

**Visual language.** A light Swiss-editorial canvas (`#F7F9FC`), Geist and Geist Mono to match the app, hairline dividers, generous margins. Real app footage is the anchor. It sits in a thin, borderless browser frame and is punched in on the area being discussed, so text stays readable at 1080p. Motion graphics only explain *relationships*: scattered files converge, PDF text becomes fields, a forecast line draws, a gap opens between "days of supply" and "lead time", an equation resolves into a case-rounded quantity, a draft PO assembles.

**The color rule, used the same way everywhere:** **deterministic blue `#3478F6`** for anything calculated, **AI ember `#E86A4A`** for anything a model reads or writes, **evergreen `#289879`** only for the human approval. Indigo `#4F67E8` is the brand accent. One restrained critical red (the app's own `#D94F61`) appears exactly once, for the risk. A small legend ("● Calculated  ● AI") stays in the lower-left corner during the product scenes (S05–S09), the same way the app's sidebar shows it.

**Voice: the product as planned, told as a working product.** The narration and titles describe StockPulse in confident present tense, as the complete solution in the planning documents (connected intake, AI document extraction, forecasting, risk, budget-aware replenishment, and the procurement agent on AMD Developer Cloud). Status chips and "designed to…" hedges are gone from the picture and the voice.

**What keeps it truthful:**
1. **Captured footage is never altered to show a result the app didn't produce.** No fake "AI extracted" or "Sent to supplier" states, no fabricated AMD/GPU telemetry, and no hidden or painted-over app labels. Punch-ins are framed for readability, and an app label that falls inside the frame stays.
2. **AI steps (extraction in S05, the agent briefing in S09) are motion graphics, not screen captures.** They're drawn in the film's own explanatory style, outside the browser frame, so they read as "how StockPulse works", not as a recording of a live model run.
3. **One quiet disclosure line** sits in the S11 architecture footer (about 18 px, on screen for 4 s or more): *"Prototype shown on sample data · AI layer on AMD Developer Cloud rolling out per the implementation plan."* Real app screens keep the app's own small "Sample dataset" mark.

**Transitions.** Mostly soft cross-dissolves (0.5 s) and one consistent *push-through* (the camera eases into the app frame) at the start of the product section (S04→S05). No whips, glitches, or 3D.

**Audio.** An original, slow ambient pad (synthesized locally, no third-party music) ducks under the narration. There are six sparse sound effects: paper slide (S02, S05), a soft data texture (S05), a tonal rise (S06, S08), one muted alert tick (S07), and one quiet two-note confirmation (S09). Full details are in `audio_cue_sheet.md`.

**Runtime:** 3:42 (222 s), against a hard limit of 3:45. VO starts 0.5 s into each scene window. Estimated speech is about 154 s, leaving roughly 68 s of breathing room in total.

---

## Frame table

| # | Time | Beat | On screen | Why (traced to the message) |
|---|---|---|---|---|
| S01 | 0:00–0:15 | Hook | A hairline balance beam tips between "Order too little → empty shelf" and "Order too much → cash in the stockroom" | Sets up the single trade-off the product resolves |
| S02 | 0:15–0:38 | Problem | The four real demo artifacts (POS CSV, Angkor PDF, port-delay email, invoice) drift apart; a "5 → 8 days" line fails to reach the reorder sheet | "Disconnected operational data" made visible |
| S03 | 0:38–0:55 | Stakes | Three line-drawn panels: stockout, trapped capital, margin erosion, each anchored by a sample-store figure | Why the disconnection costs money |
| S04 | 0:55–1:10 | Promise | StockPulse logo resolves; promise line; the camera pushes into the real Overview | States the value claim by the 4th beat |
| S05 | 1:10–1:28 | Intake | Real Supplier Inbox review of `Angkor_Beverage_Revised_Terms.pdf`; ember fields lift out of the PDF; human "Confirm" | "Connects… supplier PDFs"; human stays in control |
| S06 | 1:28–1:47 | Forecast | Real Cola forecast chart; line and 80% band draw; SMA-14 baseline comparison | "Dedicated time-series models", explainable |
| S07 | 1:47–2:05 | Risk | The days-of-supply bar (5.7 d) falls short of the lead-time bar (8 d); cut to the real Risk Radar "Critical" row | Business consequence of the supplier change |
| S08 | 2:05–2:28 | Optimize | Equation 486 + 429 + 174 − 350 → 740 → **744**; real what-if: budget $12,000 → $8,400 | "Budget-aware", deterministic |
| S09 | 2:28–2:45 | Agent + human | Ember briefing card drafts; PO-00001 assembles; real Draft → Pending → **Approved** with approver key | "Explainable"; the human approves |
| S10 | 2:45–3:05 | Features + users | Five capability nodes connect into one line; three user types | Whole workflow, not a feature list; who it's for |
| S11 | 3:05–3:28 | Architecture | Blue deterministic core, ember AI layer inside an "AMD Developer Cloud · Instinct · ROCm" boundary, human gate | Technical credibility + data privacy |
| S12 | 3:28–3:42 | Close | Logo lockup, tagline, quiet end | Product-led close |

---

## Frame 1: Hook (0–15s)

- act: Act 1: The bet
- status: animated
- duration: 15s
- transition_in: cut (fade from white over 0.4 s)
- src: compositions/frames/s01-hook.html
- scene: A hairline balance beam tips between two outcomes
- voiceover: "Every week, a store owner makes the same bet. Order too little, and the shelf runs empty. Order too much, and cash sits in the stockroom."
- vo_file: VO_01_HOOK.mp3
- on_screen_tag: none
- sfx: none; the music bed fades in from silence over 3 s
- poster: 9

The scene opens on an empty `#F7F9FC` canvas and a single ink hairline. Small type in Geist Mono reads `MONDAY · 07:30`, the app's demo session clock. A balance beam draws from the center. On "Order too little" the left pan dips: a line-drawn shelf with three facings that empty one by one, labeled **"Empty shelf"**. On "Order too much" the beam tips right: stacked case outlines pile up, labeled **"Cash in the stockroom"**. The beam settles, slightly unbalanced, and holds. Headline type is 64 px, ink color. There are no numbers yet. Motion: a slow beam pivot (power2.inOut, 1.2 s) and a staggered stroke draw-on.

## Frame 2: Problem (15–38s)

- act: Act 1: The bet
- status: animated
- duration: 23s
- transition_in: crossfade 0.5s
- src: compositions/frames/s02-problem.html
- scene: Four real demo documents drift apart; the supplier change never reaches the reorder sheet
- voiceover: "The information for a better decision already exists. It's just scattered. Sales live in the point-of-sale system. Supplier changes arrive as PDFs, invoices, and emails. When a distributor adds three days to delivery, that news rarely reaches the reorder sheet."
- vo_file: VO_02_PROBLEM.mp3
- on_screen_tag: none
- sfx: paper slide ×2 (soft), when the PDF and email cards land
- poster: 18

Four white cards with hairline borders and gentle shadows, each built from real demo material: **`sales.csv`** (the real header `date, sku, units` plus 3 real rows of SKU008), **`Angkor_Beverage_Revised_Terms.pdf`** (with its real quoted line *"standard delivery is 8 days from order"*), the email **"Re: Port congestion, revised delivery schedule"** (Siam Snacks Import), and **`INV-20931_PhnomPenhHousehold.pdf`**. They arrive one per spoken item and settle into four separate corners. Dashed connector lines try to join them and break off. On "adds three days to delivery" the phrase **"5 days → 8 days"** is highlighted inside the PDF card, travels toward a simple "Reorder sheet" card, and fades out halfway. The reorder sheet still reads `Lead time: 5 d`.

## Frame 3: Why it matters (38–55s)

- act: Act 1: The bet
- status: animated
- duration: 17s
- transition_in: crossfade 0.5s
- src: compositions/frames/s03-stakes.html
- scene: Three panels: stockout, trapped capital, margin erosion
- voiceover: "That gap is expensive. A stockout sends customers elsewhere. An over-order traps working capital. A missed price increase quietly erodes margin."
- vo_file: VO_03_STAKES.mp3
- on_screen_tag: footnote "Sample dataset · Phnom Penh Central demo store"
- sfx: none (music only, a slight swell)
- poster: 50

A three-column Swiss grid with thin vertical rules. Each column has a line-drawn icon, a one-word title and one calculated figure from the demo store's Overview: **Stockout**: *"4 products run out before a delivery can arrive"*; **Trapped capital**: *"$42,775 in stock beyond 90 days of cover"*; **Margin erosion**: *"$1.22 → $1.14 margin per can of Cola if Angkor's price rise goes unnoticed"* (shelf price $2.50 minus cost $1.28 → $1.36). The figures count up from 0 in blue (they are calculated values), and a footnote reads *"Sample dataset · Phnom Penh Central demo store · calculated by StockPulse"*. No savings claims and no industry statistics.

## Frame 4: Introducing StockPulse (55–70s)

- act: Act 2: One decision
- status: animated
- duration: 15s
- transition_in: crossfade 0.6s
- src: compositions/frames/s04-intro.html
- scene: Logo resolves, promise line, push into the real Overview
- voiceover: "StockPulse turns disconnected sales and supplier data into explainable, budget-aware purchasing decisions, without replacing the systems a retailer already uses."
- vo_file: VO_04_INTRO.mp3
- on_screen_tag: none (the app shows its own "Sample dataset" mark)
- sfx: soft transition swish when the push begins
- footage: C01 `overview` still + full-page still (camera scroll)
- poster: 60

`standard_transparent_logo.png` (cropped to its artwork) fades and sharpens in at center, 560 px wide. Beneath it, the promise line appears word by word in 40 px ink: **"Explainable, budget-aware purchasing decisions."** Then a smaller line: *"On top of the POS, spreadsheets and supplier documents you already have."* The logo moves up and shrinks to the corner, and the camera eases into a borderless browser frame showing the real **Inventory Command Center** ("19 of 34 products are stable, but 7 purchasing decisions need attention"). The push-through ends with a slight zoom on the briefing headline.

## Frame 5: Data intake and supplier-document extraction (70–88s)

- act: Act 2: One decision
- status: animated
- duration: 18s
- transition_in: push-through (continues from S04)
- src: compositions/frames/s05-intake.html
- scene: Real Supplier Inbox review; ember fields lift out of the Angkor PDF; a person confirms
- voiceover: "Take one decision. Angkor Beverage sends revised terms: delivery goes from five days to eight, and the cost of Cola rises eight cents a can. StockPulse turns the document into structured fields, and nothing changes until a person confirms them."
- vo_file: VO_05_INTAKE.mp3
- on_screen_tag: none. Extraction is drawn as a motion graphic (ember); the review and confirm steps are real app screens
- sfx: paper slide (PDF arrives), soft data texture under the field lift (≈2 s), a soft tick on Confirm
- footage: C02 state sequence: open doc → scroll the review lines → uncheck the unmatched and low-confidence lines → Confirm → "Verified"
- poster: 80

On the left, a stylized page of the PDF shows the real quoted line *"Owing to fleet maintenance, standard delivery is 8 days from order until further notice."* and the row *"Cola 330ml can, tray of 24 · $1.36"*. Ember-outlined field chips lift off the page: `lead_time_days: 8`, `unit_cost: 1.36`, `pack_size: 24`, `moq: 48`, each with its real confidence (90%, 97%, 99%, 95%). They dock into the real review form on the right, where the app's own note appears: **"Changes trusted cost $1.28 → $1.36 (+6.3%)."** Then two real guardrails are briefly highlighted: the unmatched *Lychee Soda* line ("No matching product") and the *58%* low-confidence case pack, both unchecked by the user. The cursor clicks **Confirm**, the stepper reaches **Verified**, and the chip on the fields turns from ember to blue: the data is now trusted.

## Frame 6: Demand forecasting and baseline comparison (88–107s)

- act: Act 2: One decision
- status: animated
- duration: 19s
- transition_in: crossfade 0.5s
- src: compositions/frames/s06-forecast.html
- scene: Real Cola forecast; line and 80% band draw; SMA-14 baseline comparison
- voiceover: "Next, demand. Dedicated time-series models, not a language model, forecast each product. Cola should sell about eight hundred sixty units over the next two weeks, scored against a simple moving-average baseline."
- vo_file: VO_06_FORECAST.mp3
- on_screen_tag: none
- sfx: a subtle rising tone as the forecast line draws
- footage: still `07-forecast-cola.png` (captured without the toast), punch-in on the chart and metrics
- poster: 98

A punch-in on the real chart (56 days of history, then 14 forecast days). An overlay redraws the blue forecast line and the light-blue 80% band in sync with the narration, over the real chart. Three blue callouts appear: **"861 units · next 14 days"**, **"80% range 754–968"**, **"Model: seasonal smoothing, damped trend"**. On "baseline" a small comparison card slides in: **"Held-out WAPE · Cola: model 28.8% vs 14-day average 31.8%"**, with a caption in small type: *"Lower is better · sample data · selected per product by held-out error."* A tag reads *"No language model produces these numbers"* (the app's own wording).

## Frame 7: Risk detection (107–125s)

- act: Act 2: One decision
- status: animated
- duration: 18s
- transition_in: crossfade 0.5s
- src: compositions/frames/s07-risk.html
- scene: The days-of-supply bar falls short of the lead-time bar; cut to the real Risk Radar "Critical" row
- voiceover: "Now the consequence. At eight days, the stock on hand and on order no longer lasts. Fixed rules flag Cola as critical: it runs out more than two days before a new delivery can arrive."
- vo_file: VO_07_RISK.mp3
- on_screen_tag: none
- sfx: one muted alert tick when the gap turns red (the only alert in the film)
- footage: still `08-risk-cola.png` (captured without the toast)
- poster: 116

Two horizontal timeline bars on a day ruler. Top (blue): **"110 on hand + 240 on order ÷ 61.3 a day = 5.7 days of supply"**. Bottom: **lead time**, which first draws at the old **5 d** and is fully covered, then extends to **8 d** on "At eight days". The uncovered **2.3-day** gap fills with the single critical red and is labeled *"Shelf empty before the next delivery"*. The rule is shown in mono: `stock + on order < demand × lead time  →  stockout risk`. Then a cut to the real Risk Radar row: **Critical · Cola 330ml · "Projected to run out 2.3 days before a new delivery" · lead 8d · $161 gross margin at risk**, with its tag "checked against fixed rules… never from a model's judgement".

## Frame 8: Replenishment optimization and budget trade-offs (125–148s)

- act: Act 2: One decision
- status: animated
- duration: 23s
- transition_in: crossfade 0.5s
- src: compositions/frames/s08-optimize.html
- scene: Equation resolves to 744 cans; real what-if: budget $12,000 → $8,400
- voiceover: "How much to buy? Deterministic math: demand over the lead time and review period, plus safety stock, minus what's already coming, rounded to full cases. Seven hundred forty-four cans. Cut the budget by thirty percent, and critical items stay covered while lower-priority lines give up safety stock first."
- vo_file: VO_08_OPTIMIZE.mp3
- on_screen_tag: none
- sfx: soft tonal step as each term lands; a gentle settling tone on the budget change
- footage: C06 state sequence: Load plan → what-if −30% → simulated plan compare
- poster: 134

Part 1 (≈10 s): the app's own "Why this quantity?" equation, rebuilt large in blue tiles that land on each spoken term: **486** demand over 8-day lead time **+ 429** demand over 7-day review **+ 174** safety stock **− 350** stock + on order **= 740** needed **→ 744**, *rounded to cases of 24, MOQ 48*. The final tile is outlined and labeled **744 cans · $1,011.84 at $1.36**.

Part 2 (≈12 s): real Purchasing Cart footage. A budget readout shows **Weekly budget $12,000 · proposed $9,714.28**. The **−30%** chip is clicked, and the simulator shows **Simulated plan $8,355.02 · Critical SKUs protected 5 of 5**, with the real trade-off lines **Dish Soap 750ml 260 → 190** and **Body Lotion 300ml 318 → 132**, both *"reduced: no safety stock"*. Cola's line stays at 744. A punch-in holds on "5 of 5".

## Frame 9: Procurement agent and human approval (148–165s)

- act: Act 2: One decision
- status: animated
- duration: 17s
- transition_in: crossfade 0.5s
- src: compositions/frames/s09-agent.html
- scene: Ember briefing card; PO-00001 assembles; real Draft → Pending → Approved
- voiceover: "The procurement agent explains the trade-off in plain English and prepares a purchase order draft. It explains the numbers; it never invents them. And it can't approve. A person reviews and signs off."
- vo_file: VO_09_AGENT.mp3
- on_screen_tag: none. The briefing card is a motion graphic (ember) outside the browser frame; the PO flow is real app screens, ending at "Approved · ready to dispatch" (never "Sent")
- sfx: a quiet two-note confirmation exactly when the status turns **Approved** (the only "success" sound)
- footage: C07 state sequence: generate drafts → open PO-00001 → Submit → approver key → Approve → status "Approved · ready to dispatch"
- poster: 160

Left: an ember-outlined briefing card writes itself line by line. Every number in it is shown as a **blue token** pulled from the scenes before, so the viewer sees that the agent only places calculated values: *"Cola 330ml will run out [2.3 days] before Angkor's new [8-day] delivery. Order [744] cans at the new [$1.36] cost. Within the [$8,400] budget, Dish Soap and Body Lotion give up safety stock first."* (A motion graphic of how the agent works. The wording uses only values calculated in the earlier scenes.) On "prepares a purchase order draft" a PO document assembles from the card: **PO-00001 · Angkor Beverage Co · Cola 330ml · 744 × $1.36 = $1,011.84**. On "it can't approve" a padlock outline appears over a greyed "Approve" button inside the agent card. Then real footage: Submit → approver key → **Approve** → the status pill turns **evergreen: "Approved · ready to dispatch"**, with the app's own line visible: *"No dispatch integration is connected… nothing reaches the supplier."*

## Frame 10: Core features and target users (165–185s)

- act: Act 3: Why it's credible
- status: animated
- duration: 20s
- transition_in: crossfade 0.5s
- src: compositions/frames/s10-features.html
- scene: Five capabilities connect into one line; three user types
- voiceover: "One connected workflow: supplier and sales intake, transparent forecasting, risk detection, constraint-aware replenishment, and an agent that explains its work. Built for independent retailers, specialty grocers, and small wholesalers already running a POS or spreadsheet."
- vo_file: VO_10_FEATURES.mp3
- on_screen_tag: none
- sfx: a light swish as the line completes
- poster: 172

Five nodes on one horizontal hairline, each with a tiny thumbnail cropped from that scene's real footage: **Intake** (ember+blue) → **Forecast** (blue) → **Risk** (blue) → **Replenish** (blue) → **Explain & draft** (ember) → a final evergreen **Approve** node, slightly separated. A soft dot travels the line once, carrying "Cola 330ml". On "Built for" the line rises and three typographic user cards appear below it: **Independent retailers & mini-marts**, **Specialty grocers**, **Small wholesale distributors**, with the footnote *"100 to 10,000+ SKUs · already on a POS or spreadsheet · no ERP migration."*

## Frame 11: Technical architecture and AMD infrastructure (185–208s)

- act: Act 3: Why it's credible
- status: animated
- duration: 23s
- transition_in: crossfade 0.5s
- src: compositions/frames/s11-architecture.html
- scene: Blue deterministic core, ember AI layer in an AMD boundary, human gate
- voiceover: "Under the hood, the line is strict. Forecasts, risk rules, and quantities are deterministic, auditable code. Language models on AMD Developer Cloud, with AMD Instinct GPUs and ROCm, read documents and explain results, so pricing and margin data stays private."
- vo_file: VO_11_TECH.mp3
- on_screen_tag: the disclosure footer (see "What keeps it truthful")
- sfx: none (the music carries it)
- poster: 200

A clean architecture diagram built on a 12-column grid, which assembles left to right:
- **Inputs:** `sales.csv · inventory.csv · suppliers.csv` and *supplier PDFs, invoices, emails*.
- **Deterministic core (blue, solid border):** *Forecast engine* (statistical time-series models chosen by held-out error) · *Risk rules* (stockout, expiry, excess, margin) · *Replenishment* (order-up-to policy, safety stock, case/MOQ rounding, budget priority). 
- **Backend (thin grey band under the core):** *API, unified inventory database, ingestion*.
- **AI layer (ember, dashed border):** *Document extraction* (multimodal open-weight model) · *Procurement agent* (plans tool calls over the deterministic tools; explains, never computes).
- An outer boundary around the AI layer reads **AMD Developer Cloud · AMD Instinct GPUs · ROCm · open-weight models**, and a lock glyph says *"pricing and margin data stays on private infrastructure."*
- **Footer:** the disclosure line, in small ink-2 type.
- **Human gate (evergreen):** *Approver key → PO approved* → **Purchase order** (dispatch to supplier email / webhook / Evolus AI).

On "line is strict" a vertical divider pulses once between blue and ember. The arrows show that the AI layer only *reads from* and *calls* the deterministic tools; it never writes quantities.

## Frame 12: Closing (208–222s)

- act: Act 3: Why it's credible
- status: animated
- duration: 14s
- transition_in: crossfade 0.8s
- src: compositions/frames/s12-close.html
- scene: Logo lockup, tagline, quiet end
- voiceover: "Fewer empty shelves. Less cash stuck on the floor. Decisions you can explain. StockPulse."
- vo_file: VO_12_CLOSE.mp3
- on_screen_tag: none
- sfx: none; the music resolves on its last chord and fades out over 4 s
- poster: 218

The balance beam from S01 returns once, now level, then dissolves into the centered logo (`standard_transparent_logo.png`, 640 px). Below it is the tagline **"Purchasing decisions you can explain."** and a small line in Geist Mono: *"Inventory intelligence & procurement · on AMD Developer Cloud"*. Hold, then fade to `#F7F9FC` (not black) over the final second.

---

## Playwright shot list (production capture after approval)

Capture setup: viewport **1600×900 CSS px at deviceScaleFactor 1.2 → 1920×1080 frames**; Chromium; throwaway engine (`DB_PATH=<scratch>/capture.db`, port 8811), reset before every take. Wait for toasts to clear before each still.

**Capture method: state sequences, not screen recordings.** Playwright's video recorder runs at about 25 fps, which would judder on a 60 fps timeline, and interpolating it would fake frames. So each interaction is captured as a sequence of full-resolution stills, one per real UI state (for example: inbox doc open → lines unchecked → Confirm pressed → Verified), plus a tall full-page still where a scroll is needed. HyperFrames animates between them at a native 60 fps: a scripted cursor travels to the real button, the click happens, and the next real state cross-dissolves in (120–200 ms, the app's own `--t-med`), with punch-ins and scrolls as camera moves over the still. Every state shown is a state the app actually reached during capture.

| ID | Kind | Route / actions | Used in | Inspected |
|---|---|---|---|---|
| C01 | still + full-page | `#/overview`; full-page still for a camera scroll to Priority purchasing | S04 | ✔ `01-overview.png` |
| C02 | state seq (5) | `#/inbox` → open `doc-angkor-pl` → scroll lines → uncheck a5, a4 → Confirm → Verified | S05 | ✔ `03`–`06` |
| C03 | still | `#/forecasts?sku=SKU008` (wait for toast to clear) | S06, S10 thumb | ✔ `07-forecast-cola.png` |
| C04 | still | `#/risk?sku=SKU008` | S07, S10 thumb | ✔ `08-risk-cola.png` |
| C05 | still | Cart "Why this quantity?" for SKU008 (at $12,000 budget) | S08 reference | ✔ `13-cart-why-cola.png` |
| C06 | state seq (3) | `#/cart` → Load plan → `−30%` → hold on the simulated-plan compare | S08 | ✔ `10`–`11` |
| C07 | state seq (5) | Generate drafts → PO-00001 (Angkor) → Submit → key → Approve → Approved | S09 | ✔ `16`–`20` |
| C08 | still | PO-00001 detail, Dispatch panel ("nothing reaches the supplier") | S09 | ✔ `20-po-approved.png` |
| C09 | still | Assistant panel asking *"Why is Cola 330ml at risk?"* (typed, not the default suggestion) | S09 reference / optional | ⚠ default suggestion was Peanuts; typing needed |
| C10 | still | `#/settings` integrations ("Document extraction … Not connected · Planned") | S11 reference | ✔ `23-settings-integrations.png` |

Footage note: S08 and S09 use a cart **without** the manual 500 → 480 quantity edit that the e2e test performs, so the PO line stays at the recommended **744** throughout the story.
