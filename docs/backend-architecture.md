# StockPulse backend architecture

Status: **Phase 0, for team review.** The shared contract is `stockpulse-backend/docs/CONTRACT.md`, specified in detail in [api-contract.md](api-contract.md).
The backend adapts to that contract. Open decisions are in [integration-checklist.md](integration-checklist.md).

## 1. Audit: two backends exist

| | `stockpulse-backend/` (sibling folder, not a git repo) | `agentic-replenish/app/` (this repo) |
|---|---|---|
| Contract | **Implements the shared CONTRACT.md** | Its own shape (`products[]`, `/api/pos/*`), which today's `frontend/` calls |
| Stack | FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2 + pydantic-settings, Postgres via `DATABASE_URL` (SQLite default) | FastAPI, raw `sqlite3`, untyped `dict` bodies |
| Data in | `products.csv` + `sales.csv` (aliases accepted), censored-demand normalizer, supplier PDF/image | `sales.csv` + `inventory.csv` + `suppliers.csv` |
| Engines | `app/engines/`: seasonal damped Holt vs SMA-14, rule-based risk, **PuLP/CBC MILP**; swappable via `stockpulse_ds` | `app/tools/`: 4 forecasters chosen by WAPE, risk rules, order-up-to policy, greedy budget heuristic |
| Extraction | `services/extractor.py`: LLM (OpenAI-compatible) with strict JSON, then a rules fallback. **Auto-applied.** | Simulated client-side fixtures, plus a human review/confirm flow |
| PO | Jinja2 → PDF (xhtml2pdf), draft → **approve = send** (SMTP / Evolus webhook / dry-run `.eml`) | draft → submit → approve/reject/return → mark sent → acknowledge; dispatch simulated only |
| Agent | tool registry + chat + briefing, with a deterministic fallback | tool registry + agent loop + grounded assistant |
| Tests | 13 pytest, passing (run 2026-10-18 on Python 3.12 from a scratch copy) | 16 pytest + Playwright, passing |

Both backends already have the layering we asked for. The sibling's version:
`main.py` (router + request models) · `models.py`/`db.py` (persistence) · `services/etl.py` (ingest + normalization) ·
`engines/` (analytics adapters + reference engines) · `services/po.py` (PO + PDF) · `services/dispatch.py` (email/webhook) ·
`services/agent.py`, `llm.py` (LLM/tool calling). It lacks **response** models: routes return dicts.

**Recommendation (decision T4):** make the sibling backend the backend. It already implements the shared contract and most
of Developer 1's scope. Move it into this repo, serve `frontend/` from it, and port only the endpoints the
current UI needs that the contract lacks (api-contract §8), named in contract style. Retire `app/` once `frontend/` no longer calls it.
Rebuilding the shared contract on top of `app/` would duplicate work that already exists and passes tests.

## 2. Engine adapter (Data Scientist boundary)

The interface the team already shares (`stockpulse-backend/app/engines/interface.py`):

```python
@dataclass
class SkuInput:
    sku_id: str; name: str; supplier_id: int | None; supplier_name: str; category: str
    stock: int; on_order: int
    unit_cost: float          # cost we would pay today (new cost once effective)
    list_cost: float          # contract cost on file
    new_cost: float | None; cost_effective_date: date | None
    retail_price: float; moq: int; pack_size: int; lead_time_days: int; max_stock: int | None
    history: list[tuple[date, float]]       # normalized demand (stockout days imputed)
    raw_history: list[tuple[date, float]]   # raw POS units

@dataclass
class OptimizerParams:
    budget_cap: float; horizon_days: int = 14; review_days: int = 7
    service_z: float = 1.65; forward_buy_weeks: int = 1; demand_multiplier: float = 1.0

# package `stockpulse_ds` on PYTHONPATH:
def forecast_all(skus: list[SkuInput], as_of: date, horizon: int) -> dict[str, dict]: ...      # sku_id -> Forecast (api-contract §4)
def detect_risks(skus: list[SkuInput], forecasts: dict, as_of: date, demand_multiplier: float) -> list[dict]: ...  # Risk[]
def optimize_cart(skus: list[SkuInput], forecasts: dict, risks: list, params: OptimizerParams, as_of: date) -> dict: ...  # Cart
```

**Fields the backend itself reads.** These are hard dependencies. Everything else passes through to the frontend unchanged.

| Producer | Field | Read by |
|---|---|---|
| `forecast_all` | `daily_mean` | reference risk + optimizer |
| `forecast_all` | `daily_std` | reference optimizer (safety stock, service level) |
| `forecast_all` | `metrics.model_mape`, `metrics.baseline_mape`, `metrics.improvement_pct` | `kpis`, `telemetry.baseline_accuracy` |
| `forecast_all` | `history` key | removed in what-if |
| `detect_risks` | `type`, `severity`, `revenue_at_risk`, `capital_locked` | `kpis` |
| `detect_risks` | `sku_id`, `type`, `severity`, stockout `days_of_supply` | reference optimizer (`_primary_risk`, `_reason`) |
| `optimize_cart` | `total_cost`, `budget_utilization` | `kpis` |
| `optimize_cart` | `items[].sku_id, name, supplier_id, recommended_qty, unit_cost, pack_size, reason` | PO drafts + PDF |

Mixing engines (for example a DS forecaster with the reference optimizer) works only if the DS output carries the fields above.

**Known problems at this boundary (fix in Phase 1, small changes):**
1. `engines/__init__.py` imports all three functions in **one** `try … except Exception`. If DS ships only `forecast_all`, or their
   package raises any error on import (a missing dependency or a typo), the backend **silently** uses all reference engines.
   The only trace is `telemetry.engine_source == "reference"`. Fix: import per function, and add `ENGINE=ds|reference|auto`, where `ds` fails loudly.
2. No validation of DS output. A missing `daily_std` or a pack-size violation surfaces as a `KeyError`/500 or a bad PO.
   Fix: check the fields above and the cart invariants (api-contract §4) at the adapter boundary. On a violation, set
   `engine_source` to say which engine failed. Never repair numbers.
3. Supplier extraction is not part of `stockpulse_ds`. It lives in `services/extractor.py` with the prompt marked DS-owned.
   Its interface is `extract_supplier_updates(raw: bytes, filename: str, skus: dict[sku_id, unit_cost]) -> (list[Update], method)`,
   with `Update = {sku_id, new_cost?, lead_time_days?, moq?, effective_date?}` and `method` = `"amd_vllm"` or `"rules"`. There are no confidence values,
   and the prompt asks the LLM to **compute** new costs for "all products +10%" notices (an LLM producing numbers).

## 3. Persistence

Sibling tables (SQLAlchemy ORM, `init_db` → `create_all`): `suppliers`, `products`, `sales_daily` (raw + normalized + censored flag),
`supplier_updates`, `purchase_orders` (lines as JSON, `pdf_path` on disk), `settings`.
`DATABASE_URL` defaults to `sqlite:///./data/stockpulse.db`. `docker-compose.yml` runs `postgres:16-alpine` with the `psycopg2-binary` driver.
`shortcut: create_all, no migrations; add Alembic before the first schema change on a deployed Postgres`.

## 4. Dependencies

Adopting the sibling adds this repo's missing pieces with **no new packages beyond its `requirements.txt`**:
`sqlalchemy, psycopg2-binary, scipy, pulp==2.9.0, jinja2, xhtml2pdf, reportlab, pypdf, python-multipart, pydantic-settings`.
It was verified on Python 3.12, which matches this repo's Docker image. This repo's local `.venv` is Python 3.15 and **untested** with those packages.
The DS adds their own packages (for example statsforecast) to `requirements.txt` when `stockpulse_ds` lands.

## 5. Findings to act on regardless of the decision

1. **`test.py` in this repo is tracked in git (since `9bc6325`) and contains a hardcoded LLM API key.** Rotate the key and delete the file.
2. Approve = send, and with no SMTP or webhook configured the PO is marked `sent` after writing a local `.eml` (api-contract §6, T1).
3. Telemetry reports a model and "AMD Instinct GPU / ROCm / vLLM" when no endpoint is configured (T5).
4. Extracted supplier values change costs and lead times with no human review (T2). This repo's product rules require review.
5. The sibling's committed `docs/sample_*.json` (generated 2026-10-17) happen to have an empty `cart.unbought`, so the frontend gets no example of a budget-cut line.
   The demo data is anchored to today, so the outputs drift by date. Use `frontend/fixtures/` (2026-10-18, same keys plus one `unbought` line).
