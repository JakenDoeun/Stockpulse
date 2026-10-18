# Claim audit

Every claim the film makes, spoken or on screen, is checked against what was observed on 2026-10-18 when Playwright drove the local app (`app.main` on a throwaway DB, sample data, no `LLM_*` configured) and against the code and docs.

**Project status (confirmed by the project owner, 2026-10-18):** the production backend and the AI models are **not built or connected yet** and will be delivered as planned. What runs today is the **prototype**: the web UI plus local prototype logic (Python, on synthetic sample data) that produces the forecast, risk, quantity and approval states shown on screen.


**Film presentation policy (owner's direction, 2026-10-18):** the film presents StockPulse as a working product, following the planning documents, in confident present tense, without per-scene status chips. The statuses below remain the internal truth. The film stays honest in three ways:
1. Captured app footage is never altered to show a state the app didn't reach, and the app's own labels are never hidden.
2. AI steps are shown as motion graphics, not as recordings of a model run.
3. One disclosure line appears in the S11 footer.

**Legend.**
- **PROTOTYPE**: observed running in the local prototype on sample data. It's shown as real UI, never as a production result.
- **SIMULATED**: the prototype UI uses a fixture or template for this step, and the app labels it that way.
- **PLANNED**: part of the production design, not built or connected yet. The film describes it as "designed to…" and labels it `PLANNED`.

| # | Claim (where) | Status | Evidence | How the film presents it |
|---|---|---|---|---|
| 1 | Sales/inventory/supplier data in a canonical CSV schema (S02, S11) | PROTOTYPE (schema) · ingestion backend PLANNED | `app/data_sample/*.csv`; `POST /api/data/check`, `/api/data/import` exist (import not exercised in inspection) | Shown as real file names and headers |
| 2 | Supplier PDF fields (lead time 8 d, cost $1.36, pack 24, MOQ 48) are extracted by a model (S05) | **SIMULATED** | Inbox shows "Simulated extraction · sample fixture" (`frontend/src/data/demo.ts` fixture `doc-angkor-pl`) | Chip `EXTRACTION SIMULATED ON SAMPLE DOCUMENT`; VO says "turns the document into structured fields" (product design), never "AI read it live" |
| 3 | Review blocks bad lines (unmatched SKU, <80% confidence); confirming writes trusted values (S05) | PROTOTYPE | Confirm stays disabled until line a5 is excluded; afterwards `/api/dashboard` shows SKU008 `unit_cost 1.36`, `lead_time_days 8` | Real UI state sequence |
| 4 | Forecasts come from statistical models, not an LLM; best model picked by held-out WAPE (S06, S11) | PROTOTYPE logic · production forecasting service PLANNED | `app/tools/forecast.py`; `/api/forecast/SKU008` → `holt_seasonal`, candidate WAPEs listed | Real chart + callouts |
| 5 | Cola: 861 units / 14 d, 80% range 754–968, SMA-14 879 (S06) | PROTOTYPE (sample data) | Forecast page, post-confirmation | Shown as is |
| 6 | Cola held-out WAPE 28.8% vs SMA-14 31.8% (S06) | PROTOTYPE, **with caveat** | `/api/dashboard` forecast block. Across the whole catalog the backtest's next-week WAPE is about equal to a trailing mean (README caveat) | Labelled "Cola · sample data"; no "more accurate" claim in VO |
| 7 | Cola becomes Critical: 5.7 days of supply vs 8 d lead time, runs out 2.3 d before delivery, $161 margin at risk (S07) | PROTOTYPE (sample data) | Risk Radar row `stockout-SKU008` after confirmation; before the update the dashboard reason was OK | Real row + bar animation of the same numbers |
| 8 | Fixed-rule risk, not model judgement (S07) | PROTOTYPE logic | `app/tools/risk.py`; the page copy says so | Shown |
| 9 | Order quantity 744 = 486 + 429 + 174 − 350 → round to case 24 / MOQ 48 (S08) | PROTOTYPE (sample data) | Cart "Why this quantity?" for SKU008 | Rebuilt equation, the same values |
| 10 | Budget-aware: $12,000 → −30% → $8,355.02 plan, 5 of 5 critical protected, Dish Soap 260→190, Body Lotion 318→132 (S08) | PROTOTYPE (sample data) | Cart what-if simulator | Real state sequence |
| 11 | "Optimizer" / "solver" (S08, S11) | PROTOTYPE: a **greedy priority heuristic**; the MILP solver is PLANNED | README: "a stated greedy heuristic, not a MILP solver" (`app/tools/budget.py`). The plan's PuLP MILP is PLANNED | The words "solver" and "MILP" are never used; chip note "greedy priority heuristic" |
| 12 | The agent explains trade-offs in plain English (S09) | Agent model **PLANNED**; prototype assistant **SIMULATED** (templates) | Assistant panel says "Simulated assistant… templates over real calculations"; `app/agent.py` LLM loop exists but needs `LLM_*` (not configured) | VO: "is designed to explain"; briefing card labelled `CONCEPT · AGENT MODEL PLANNED`; every number in it is a prototype value from the earlier scenes |
| 13 | The agent never invents numbers (S09, S11) | Design rule; the guard exists in prototype code, the agent is PLANNED | README: LLM rewording that introduces new numbers is rejected; the agent only calls tools | Said in VO |
| 14 | The agent can't approve; a human approves with an approver key (S09) | PROTOTYPE (approval flow and key check) | No approve tool in `app/registry.py`; approve needs `X-Approver-Key`; status went Draft → Pending → Approved | Real state sequence |
| 15 | The PO is sent to the supplier (S09) | **SIMULATED** | Dispatch panel: "No dispatch integration is connected… nothing reaches the supplier"; status stays "Approved · ready to dispatch" | Chip `DISPATCH SIMULATED`; the film never shows "Sent" |
| 16 | PO-00001 line 744 × $1.36 = $1,011.84 (S09) | PROTOTYPE; **re-check at capture** | Inspection used the e2e path (edited to 480 → $652.80). The capture skips that edit | Capture asserts the line before the stills are used |
| 17 | Runs on AMD Developer Cloud / AMD Instinct / ROCm (S11, S12) | **PLANNED** | No AMD endpoint is configured in this environment; Settings shows "Document extraction (multimodal, AMD Instinct + ROCm): Not connected · Planned"; the code targets an OpenAI-compatible AMD Token Factory endpoint | VO: "designed to run on AMD Developer Cloud"; chip `PLANNED`; close says "designed for" |
| 18 | Data stays private (S11) | PLANNED (follows from #17) | Design intent in PRODUCT.md | Said as the reason for the design, not as a certified property |
| 19 | MCP interface (S11) | PLANNED | `mcp_server.py` is a placeholder; REST tool endpoints exist in prototype code only | "REST tools · MCP planned" |
| 20 | Evolus AI workflow (S11) | SIMULATED | "Evolus AI workflow · simulated" | Shown only in the diagram, labelled simulated |
| 21 | Sample-store figures: $42,775 dead-stock capital; Cola 2.3 days short of the delayed delivery; Cola margin $1.22 → $1.14 per can ($2.50 shelf price − $1.28 / $1.36 cost) (S03). v2 dropped "4 stockouts": it is the pre-update Overview count and conflicted with the post-update Risk Radar (5 Critical) | PROTOTYPE (sample data) | Overview before the supplier update; Risk Radar after it | "Sample store data" tag on the scene |
| 22 | Target users: independent retailers, specialty grocers, small wholesalers, 100–10,000+ SKUs (S10) | Positioning (from docs) | Proposal "Target Users" | Stated as who it's built for, not as customers |

## Claims intentionally left out

- Any savings, "X% fewer stockouts", or backtest deltas (`backtest/results.json` shows big deltas, but against a deliberately simple static baseline on synthetic data. The caveats wouldn't fit in a pitch film without misleading.)
- "60-second approval", "one click", "100% extraction accuracy", "zero hallucinations", or live GPU latency.
- Customer names, testimonials, logos.
- LightGBM / Prophet / PuLP / Qwen as *running* components: they appear only in the PLANNED layer of S11, or not at all.
