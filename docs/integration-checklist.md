# StockPulse integration checklist

**Gate: no Phase 1 backend work until §4 is signed by all three roles.**
Contract: [api-contract.md](api-contract.md) (the shared CONTRACT.md, specified) · Architecture: [backend-architecture.md](backend-architecture.md).

## 1. Data Scientist: confirm your actual interfaces

The backend adapts to what you actually have. Please answer from **your code**, not from CONTRACT.md. Where your
answer differs, the backend changes its adapter; you don't change your code to match ours.

**Run this first** (2 minutes). With your package on `PYTHONPATH`, run the backend tests and check which engine actually ran:
```bash
cd stockpulse-backend && PYTHONPATH=.:<path-to-your-package-parent> pytest -q
PYTHONPATH=.:<…> python -c "from app.engines import ENGINE_SOURCE; print(ENGINE_SOURCE)"   # must print stockpulse_ds
```
If it prints `reference`, your package failed to import and **the tests ran on the reference engines, not yours**: the import error is swallowed (architecture §2.1).
`test_forecast_beats_baseline_on_average` requires `avg_improvement_pct > 0`. If your model honestly doesn't beat SMA-14 on the demo data, report that. Don't tune to the test.

| # | Question | Your answer |
|---|---|---|
| **Forecasting** `forecast_all(skus, as_of, horizon)` | | |
| F1 | Exact signature, and does it take `list[SkuInput]`? If not, what input (DataFrame? columns?) | |
| F2 | Do you forecast from `history` (normalized) or `raw_history`? | |
| F3 | Do you return `daily_mean` (mean of the first 7 days) and `daily_std` (daily error σ)? Both are **required** by the optimizer and risk. | |
| F4 | Interval: which level, how is it computed, and can it be absent? (C3/C4) | |
| F5 | Metrics: MAPE and RMSE in **percent/units** as in the samples? Holdout length? Baseline = SMA-14? | |
| F6 | SKUs with short or no history: skipped, or returned with `null` metrics? | |
| F7 | Runtime for 10 / 100 SKUs, and new dependencies | |
| **Risk** `detect_risks(skus, forecasts, as_of, demand_multiplier)` | | |
| R1 | Exact signature and return type | |
| R2 | Types you emit (stockout / margin_erosion / dead_stock / overstock / other?) and per-type fields | |
| R3 | Severity scale (3 levels?) and score range | |
| R4 | Do stockout risks include `days_of_supply`, `revenue_at_risk`? Do dead-stock risks include `capital_locked`? (read by kpis/optimizer) | |
| **Optimizer** `optimize_cart(skus, forecasts, risks, params, as_of)` | | |
| O1 | Exact signature; which `OptimizerParams` fields you use; do you need ones that aren't there? | |
| O2 | Solver (PuLP/CBC, HiGHS, SciPy), time limit, and what `solver_status` you return when not optimal | |
| O3 | Do you return `items[]` and `unbought[]` with the `CartLine` fields (api-contract §4)? | |
| O4 | Constraints you enforce: pack multiple, MOQ, budget, `max_stock`, supplier minimum? | |
| O5 | Do you compute reorder point / safety stock yourself, or expect them as inputs? | |
| **Extraction** (prompt is DS-owned; code is in the backend) | | |
| E1 | Do you own only `EXTRACTION_PROMPT`, or an extraction function? Its signature? | |
| E2 | Can your extractor return per-field confidence? (needed if T2 = human review) | |
| E3 | "All products +10%" notices: should the LLM return the rule and let code compute the costs? Today the LLM computes them. | |
| **Delivery** | | |
| D1 | Will you ship all three functions together? Today a partial package silently falls back to reference for **all** of them. | |
| D2 | Package name `stockpulse_ds`, delivery location (repo path or pip), and Python version | |

## 2. Frontend: build against the mocks now

- [ ] Fixtures: `frontend/fixtures/dashboard.json`, `what_if_2500.json`, `po_draft.json` and `purchase_order.pdf`, served at `/static/fixtures/…`.
      They are reference-engine output on synthetic demo data.
- [ ] Join `forecasts`, `risks` and `cart` lines by `sku_id`, never by index (C5). Treat every N field as possibly `null` (api-contract §4).
- [ ] Gate any "AMD / model" badge on `telemetry.endpoint_configured && telemetry.calls > 0` until A4 lands (T5).
- [ ] Show `dispatch_channel == "dry_run_outbox"` as "dry run, not sent" (T1).

Today's `frontend/src/data/api.ts` routes vs the shared contract:

| Current UI call | Shared contract | Gap |
|---|---|---|
| `GET /api/dashboard` (`products[]`) | `GET /api/dashboard` (`forecasts/risks/cart/kpis`) | **Same path, different shape.** Remap in `data/` and `types.ts`. |
| `GET /api/health` | `GET /api/health` | `llm_enabled` → `llm_configured`; no `data_source` |
| `POST /api/optimize` | `POST /api/what-if` | Returns the full dashboard. Overrides are keyed by SKU (C10). |
| `GET /api/forecast/{sku}` | — | Proposed A1 |
| `POST /api/assistant` | `POST /api/agent/chat` | Different body/response |
| `/api/data/check`, `/import`, `/reset`, `/status` | `POST /api/ingest` (multipart), `/api/reset`, `/api/demo/load` | No dry-run check; different CSV schema (`products.csv`) |
| `/api/pos`, `/api/pos/{id}` | `/api/po`, `/api/po/{id}` | Different PO shape (no events/terms) |
| `POST /api/pos/drafts` (`lines[]`) | `POST /api/po/draft` (`quantity_overrides`) | |
| `/api/pos/{id}/submit\|reject\|return\|cancel\|mark_sent\|acknowledge` | only `/approve` | Proposed A2 |
| `/api/pos/{id}/dispatch` (simulated) | approve sends | T1 |
| `POST`/`DELETE /api/supplier-updates` (confirm/revert) | `GET` only; ingest auto-applies | T2, A6 |

## 3. Team decisions (product-level conflicts)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| T1 | Approve and send | (a) one step, as today; (b) approve, then explicit send | (a) is fine, **but** a dry run must not set `sent` (add A5, or a `dry_run` status) |
| T2 | Extracted supplier values | (a) applied immediately, as today; (b) held for human confirmation | (b): this repo's product principles require it, and the extractor reports no confidence |
| T3 | PO lifecycle | (a) draft/sent/failed; (b) add reject/return/cancel (A2) | (b) only if the UI keeps those pages for the demo |
| T4 | Backend codebase | (a) sibling backend moves into this repo; (b) rebuild the shared contract on `app/` | (a) |
| T5 | Telemetry | (a) as today; (b) `model`/`hardware` null unless inference actually ran (A4) | (b): otherwise the badge claims AMD inference that didn't happen |
| T6 | Demo dataset | (a) sibling demo (10 SKUs, `SKU-101`…); (b) this repo's sample (34 SKUs, 3-table CSV) | (a) for the contract and fixtures; the 3-table CSV then needs an import adapter or is dropped |

Plus the clarifications C1–C12 and additions A1–A6 in api-contract §7–§8: accept the proposed answer or amend it.

## 4. Sign-off

| Role | Name | §1 answers / §3 decisions / C1–C12 / A1–A6 | Date |
|---|---|---|---|
| Backend (Dev 1) | | | |
| Data Scientist | | | |
| Frontend | | | |

After sign-off: update `stockpulse-backend/docs/CONTRACT.md` with the agreed changes (its own version line), regenerate
`frontend/fixtures/`, and start Phase 1.

## 5. Blocking hygiene

- [ ] Rotate the LLM API key hardcoded in this repo's `test.py` (tracked since `9bc6325`), then delete the file.
