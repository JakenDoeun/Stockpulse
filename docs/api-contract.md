# StockPulse API contract

**Authority:** the shared contract is `stockpulse-backend/docs/CONTRACT.md`, which the Data Scientist and frontend already build on.
This file **does not change it**. It pins down what CONTRACT.md leaves implicit (types, units, nullability, error bodies),
read from the reference implementation (`stockpulse-backend/app`, 13/13 tests passing on 2026-10-18).

Three kinds of content, kept apart:
- **§1–§6 Contract as implemented.** Build against this.
- **§7 Clarifications.** Ambiguities the team must confirm. Each has a proposed answer that keeps today's behaviour.
- **§8 Proposed additions.** Additive only. Nothing here exists until signed off in [integration-checklist.md](integration-checklist.md).

Mock JSON for the frontend: `frontend/fixtures/` (served at `/static/fixtures/…` by this repo's app), regenerated from the reference engine on 2026-10-18:
`dashboard.json` (`GET /api/dashboard`), `what_if_2500.json` (`POST /api/what-if {"budget_cap": 2500}`), `po_draft.json` (`POST /api/po/draft {}`) and `purchase_order.pdf`.
The demo data is **synthetic** (10 SKUs, `SKU-101`…`SKU-110`) and anchored to the day it was generated, so dates and totals shift by date while the shape stays the same.

## 1. Conventions (as implemented)

| Topic | Rule |
|---|---|
| Base path | `/api/*`, unversioned. CONTRACT.md is "v1". Changing a field's meaning or removing one requires a CONTRACT.md change signed off by all three roles. |
| SKU id | `sku_id`: string, e.g. `"SKU-101"`. The same name is used on every endpoint, including request keys (`quantity_overrides`, `lead_time_overrides`). |
| Supplier id | `supplier_id`: **integer** DB id, or `null` for an unassigned supplier. Not stable across `/api/reset` (see C1). |
| PO id | `id`: integer. Display number `po_number`: `"PO-YYYYMMDD-NNN"`. |
| Business dates | `"YYYY-MM-DD"` (`as_of`, `date`, `effective_date`, `stockout_date`). `as_of` = today. History ends `as_of − 1`; forecast starts at `as_of`. |
| Timestamps | `generated_at`: ISO 8601 **with** offset (`+00:00`). PO `created_at`/`approved_at`: ISO 8601 UTC **without** offset (see C6). |
| Money | float, currency units (USD shown in UI). `unit_cost` up to 4 dp, totals 2 dp. |
| Percent vs fraction | **Percent (0–100):** `*_mape`, `improvement_pct`, `avg_improvement_pct`, `margin_*_pct`. **Fraction (0–1):** `budget_utilization`, `expected_service_level`, `avg_service_level`. **Score:** 0–100. |
| Quantities | int units. Demand is float units/day. Lead times are int days. |
| Missing values | `null`. NaN/inf are converted to `null` before sending (`pipeline._clean`). |
| Errors | **Since Phase 1 (`backend/`):** every error is `{"detail": "<message>", "code": "<CODE>", "errors": [{"loc": [...], "message": "..."}]}`. `detail` is always a string. **Change:** validation `422` previously returned `detail` as a list (`[{"loc", "msg", "type"}]`); that list now lives in `errors`, and `detail` summarises the first problem. `code` and `errors` are additions. Request bodies reject unknown fields with 422. |

## 2. Routes

| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/health` | | `{status:"ok"\|"degraded", app:{name, version, environment}, database:{status:"ok"\|"unavailable"\|"migrations_pending", backend, revision, expected_revision, detail}}` (added in Phase 1) | 503 when degraded |
| GET | `/api/health` | | `{status:"ok", products:int, llm_configured:bool, telemetry:{…}}` | |
| GET | `/api/telemetry` | | `Telemetry` | |
| POST | `/api/demo/load` | | load summary | |
| POST | `/api/reset` | | `{ok:true}` | |
| POST | `/api/ingest` | multipart (§3) | `IngestResult` | 400, 422 |
| GET | `/api/dashboard` | `?budget_cap=float&explain=bool` | `Dashboard` (§4) | 409 no data |
| POST | `/api/what-if` | `WhatIf` (§5) | `Dashboard` without `forecasts[].history` | 409, 422 |
| GET | `/api/products` | | `[{sku_id, name, category, supplier, unit_cost, retail_price, current_stock, moq, pack_size, lead_time_days}]` | |
| GET | `/api/supplier-updates` | | `SupplierConstraint[]` | |
| POST | `/api/agent/chat` | `{message:str, history:[]}` | `{answer, tool_trace, mode}` | |
| GET / POST | `/api/agent/tools`, `/api/agent/tools/{name}` | tool args | tool result | 404 |
| POST | `/api/po/draft` | `{budget_cap?:float, quantity_overrides?:{sku_id:int}}` | `{purchase_orders: PO[], briefing:str}` | 409 empty cart |
| GET | `/api/po`, `/api/po/{id}` | | `PO[]`, `PO` | 404 |
| GET | `/api/po/{id}/pdf` | | `application/pdf`, inline | 404 |
| POST | `/api/po/{id}/approve` | `{recipient_override?:str}` | `PO` + `dispatch` (§6) | 404, 409 already sent |

## 3. Ingest: `POST /api/ingest`

`multipart/form-data`. Any subset of the fields below; at least one file is required.

| Field | Type | Notes |
|---|---|---|
| `products_csv` | file | `sku_id, name, unit_cost, current_stock` required; `category, supplier, supplier_email, retail_price, moq, pack_size, lead_time_days, on_order, max_stock` optional; aliases accepted (`sku`, `cost`, `stock`, …) |
| `sales_csv` | file | `date, sku_id, units_sold` required; `stock_end` optional (used by the censored-demand normalizer) |
| `supplier_doc` | file | PDF/PNG/JPG. Needs products loaded first (else 400). **Extracted values are applied immediately** (see T2). |
| `budget_cap` | float (form) | Saved as the default budget |

Response: `{"products"?: {...}, "sales"?: {...}, "supplier_updates"?: {"method": "amd_vllm"|"rules", "skus": [sku_id], "count": int}, "constraints": SupplierConstraint[]}`.
CSV problems → `422 {"detail": "<message>"}` (`etl.IngestError`).

## 4. Dashboard: `GET /api/dashboard`

Example: `frontend/fixtures/dashboard.json`. **R** = always present and non-null; **N** = present, may be `null`; **O** = may be absent.

| Field | Type | Req | Notes |
|---|---|---|---|
| `generated_at` | timestamp | R | |
| `as_of` | date | R | |
| `budget_cap` | float | R | Query param, else the saved setting, else `DEFAULT_BUDGET` |
| `horizon_days` | int | R | Default 14 |
| `scenario` | `{lead_time_delta_days:int, lead_time_overrides:{sku_id:int}, demand_multiplier:float}` | R | Echo of what-if inputs (zeros/1.0 on the dashboard) |
| `kpis` | object | R | below |
| `supplier_constraints[]` | `SupplierConstraint` | R | Latest extracted update per SKU |
| `forecasts[]` | `Forecast` | R | **Only SKUs with sales history**, so the count can be below `skus_tracked` (C5) |
| `risks[]` | `Risk` | R | Sorted by severity, then score, descending |
| `cart` | `Cart` | R | |
| `telemetry` | `Telemetry` | R | |
| `briefing` | string | R | `""` when `explain=false`. LLM text or a template; no field says which (C7) |

**`kpis`:** `skus_tracked` int · `high_risk_count` int (risks with severity high, any type) · `imminent_stockouts` int (stockout and high) ·
`revenue_at_risk` float (Σ stockout `revenue_at_risk`) · `capital_locked_dead_stock` float (Σ dead_stock `capital_locked`) ·
`avg_model_mape` N float % · `avg_baseline_mape` N float % · `avg_improvement_pct` N float % (**mean RMSE improvement**, not MAPE; C2) ·
`cart_total` float · `budget_utilization` float 0–1.

**`SupplierConstraint`:** `sku_id` · `name` · `old_cost` N · `new_cost` N · `lead_time_days` N int · `moq` N int · `effective_date` N date ·
`source_doc` str · `extraction_method` `"amd_vllm"|"rules"` · `headline` str.

**`Forecast`:**

| Field | Type | Req | Notes |
|---|---|---|---|
| `sku_id`, `name` | str | R | |
| `daily_mean` | float | R | Mean of the **first 7** forecast days (units/day). **Read by risk + optimizer.** |
| `daily_std` | float | R | Daily forecast-error σ. **Read by optimizer** (safety stock). Reference floors it at 5% of the mean (C3). |
| `interval` | str | R | Label, e.g. `"90%"` |
| `history[]` | `{date, units:float, normalized:float}` | O | Last 60 days; omitted in what-if. `units` = POS sales; `normalized` = demand with stockout days imputed (C11). |
| `forecast[]` | `{date, mean, lower, upper}` floats | R | `horizon_days` entries; `lower ≥ 0` |
| `metrics` | object | R | `model_mape` N %, `baseline_mape` N %, `model_rmse` N, `baseline_rmse` N, `improvement_pct` N % (RMSE), `holdout_days` int (0 = not evaluated), `model` str, `baseline` str (`"SMA14"`). All N fields are `null` when history < holdout + 28 days. |
| `method_note` | str | O | Plain-language method description |

**`Risk`.** Common fields: `sku_id` · `name` · `type` `"stockout"|"margin_erosion"|"dead_stock"|"overstock"` · `severity` `"high"|"medium"|"low"` · `score` 0–100 · `message` str. Per type:

| type | Extra fields |
|---|---|
| `stockout` | `days_of_supply` float, `lead_time_days` int, `stockout_date` date, `daily_demand` float, `revenue_at_risk` float |
| `margin_erosion` | `margin_before_pct`, `margin_after_pct` float %, `old_cost`, `new_cost` float, `suggested_retail_price` N float |
| `dead_stock` | `days_since_last_sale` int (999 = never sold), `capital_locked` float |
| `overstock` | `days_of_supply` float, `capital_locked` float (in code, not in the current samples) |

**`Cart`:** `budget_cap` · `total_cost` · `budget_utilization` (0.0 when the budget is 0) · `unconstrained_cost` · `solver_status` str (`"Optimal"`, other PuLP status, `"greedy_fallback"`, `"no_orders_needed"`) · `avg_service_level` N · `items[]` · `unbought[]`.

| `CartLine` field | Type | items | unbought |
|---|---|---|---|
| `sku_id`, `name`, `supplier_name`, `risk`, `risk_severity`, `reason` | str | R | R |
| `supplier_id` | int \| null | R | R |
| `unit_cost`, `reorder_point`, `safety_stock`, `daily_demand`, `line_cost` | float | R | R (`line_cost` 0.0) |
| `pack_size`, `moq`, `units_needed`, `current_stock`, `lead_time_days`, `recommended_qty` | int | R | R (`recommended_qty` 0) |
| `packs` | int | R | — |
| `expected_service_level` | float 0–1 | R | — |
| `days_of_cover_after` | float | R | — |

`risk` is the line's primary risk type or `"none"`; `risk_severity` is a severity or `"none"`. Invariants enforced by tests:
`total_cost ≤ budget_cap`, `recommended_qty % pack_size == 0`, `recommended_qty ≥ moq`, `line_cost == recommended_qty × unit_cost`.

**`Telemetry`:** `model` str · `endpoint_configured` bool · `endpoint_host` N · `hardware` str · `calls` int · `last_latency_s` N · `last_tokens_per_sec` N ·
`total_completion_tokens` int · `last_error` N · `engine_source` `"stockpulse_ds"|"reference"` · `pipeline_compute_ms` int · `baseline_accuracy` `{model_mape, baseline_mape}`.
`model`/`hardware` are configuration labels and are filled in **even when no LLM is configured** (T5).

## 5. What-if: `POST /api/what-if`

```json
{"budget_cap": 2500, "lead_time_delta_days": 0, "lead_time_overrides": {"SKU-102": 9}, "demand_multiplier": 1.0, "explain": false}
```
All fields optional. `budget_cap` ≥ 0 (default: saved budget). `lead_time_delta_days` int, added to every SKU. `lead_time_overrides` maps **sku_id** → days (overrides the delta).
`demand_multiplier` > 0 (scales demand in risk and optimizer, not in `forecasts[]`). Returns the `Dashboard` shape without `history`. Example: `frontend/fixtures/what_if_2500.json`.

## 6. Purchase orders

**`PO`:** `id` int · `po_number` str · `supplier` str · `supplier_email` str · `status` `"draft"|"sent"|"failed"` · `total` float ·
`lines[]` `{sku_id, name, recommended_qty, unit_cost, line_cost, pack_size, reason}` · `pdf_url` str · `dispatch_channel` str (comma-joined) ·
`dispatch_detail` str · `created_at` timestamp · `approved_at` N timestamp.

`POST /api/po/draft` re-runs the optimizer, applies `quantity_overrides` to `cart.items` only (clamped at ≥ 0, **not** re-checked against pack/MOQ, see C12), groups lines by supplier, and writes one PDF per draft.
Example: `frontend/fixtures/po_draft.json`.

`POST /api/po/{id}/approve` **approves and sends in one step**. It is the human gate. Response = `PO` plus
`dispatch: {"ok": bool, "results": [{"channel": "evolus_webhook"|"smtp"|"dry_run_outbox", "ok": bool, "detail": str}]}`.
`status` becomes `"sent"` if any channel succeeded, else `"failed"`. A failed PO can be approved again. Approving a PO that is already `sent` → 409.
**With no SMTP or webhook configured, the channel is `dry_run_outbox`, it counts as success, and the PO is marked `"sent"` although nothing left the machine** (T1).

## 7. Clarifications to confirm (proposed answer keeps current behaviour)

| # | Question | Proposed answer |
|---|---|---|
| C1 | `supplier_id` is a DB autoincrement and changes after `/api/reset`. Safe as a key? | Yes within one dataset. The frontend must not persist it across resets. |
| C2 | `avg_improvement_pct` sits next to MAPE but is RMSE-based. | Keep it. The UI labels it "RMSE improvement vs SMA-14". |
| C3 | The reference floors `daily_std` at 5% of the mean, so part of the band is assumed. | DS confirms the floor or removes it. `method_note` states it. |
| C4 | What if a DS model has no interval? | `lower`/`upper` = `null` and `interval` = `null`. The UI draws no band. **The optimizer still needs `daily_std`.** |
| C5 | `forecasts[]` skips SKUs with no history. | The frontend joins by `sku_id` and never by index. |
| C6 | PO timestamps lack an offset. | They are UTC. Adding `Z` later is additive. |
| C7 | `briefing` doesn't say LLM vs template. | Add `briefing_source` (§8, A3). |
| C8 | Severity has 3 levels; this repo's UI uses 4 (critical/high/medium/low). | The UI maps to 3. |
| C9 | `overstock` exists in code but not in the samples. | The frontend handles it anyway. |
| C10 | `lead_time_overrides` is keyed by SKU, while this repo's UI keys by supplier. | Keep SKU. The UI expands a supplier choice to its SKUs. |
| C11 | `history[].normalized` contains imputed values. | The UI labels it "estimated demand", distinct from sales. |
| C12 | `quantity_overrides` aren't checked for pack/MOQ, and overrides for SKUs in `cart.unbought` are **silently ignored** (only `items` are read). | The backend rejects invalid or ignored overrides with 422 (behaviour change, needs sign-off). |

## 8. Proposed additions (additive; need sign-off before anyone builds on them)

| # | Addition | Why |
|---|---|---|
| A1 | `GET /api/forecast/{sku_id}`: holdout actuals vs model vs baseline series, plus model candidates | This repo's Demand Forecasts page needs it, and `forecasts[]` has only summary metrics |
| A2 | PO lifecycle actions `POST /api/po/{id}/{reject\|return\|cancel}` and `status` values to match | This repo's Purchase Orders page has them. Contract today: draft → sent/failed only. |
| A3 | `briefing_source: "llm"\|"template"\|null` at top level | Provenance label (C7) |
| A4 | `telemetry.model`/`hardware` = `null` unless `endpoint_configured` and `calls > 0` | Prevents an "AMD" badge for inference that didn't run (T5) |
| A5 | `dispatch.results[].delivered: bool` (`false` for `dry_run_outbox`) | The UI must not say "sent to supplier" for a dry run (T1) |
| A6 | `supplier_constraints[].status: "pending_review"\|"confirmed"` and `POST /api/supplier-updates/{id}/confirm` | Only if T2 is decided in favour of human review |
