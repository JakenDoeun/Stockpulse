# Agentic Replenishment Copilot

Three plug-in tools + an LLM orchestrator + a human-approval gate, for the AMD hackathon Track 3.

```
Other apps / Evolus / MCP clients ──► REST  POST /api/tools/{name}
                                          │
        Orchestrator agent (LLM on AMD Token Factory, OpenAI-compatible tool calling)
           │ plans · explains · writes PO rationale        (never computes numbers)
   ┌───────┼────────────────┬──────────────────────┐
forecast_demand   detect_inventory_risk   optimize_replenishment     ← deterministic code
   └───────┴────────────────┴──────────────────────┘
                  canonical CSV schema (sales · inventory · suppliers)
                              │
        create_purchase_order_drafts → status PENDING → human approves (X-Approver-Key)
```

## Run

```bash
pip install -r requirements.txt
python -m app.data_gen                 # (re)generate sample data, already included
python -m backtest.run_backtest        # writes backtest/results.json (shown in the dashboard)
cp .env.example .env                   # fill LLM_BASE_URL / LLM_API_KEY / LLM_MODEL from AMD Token Factory
uvicorn app.main:app --reload          # http://localhost:8000
pytest -q                              # 8 tests
# or: docker compose up --build
```
With no `LLM_*` variables the app runs in **offline mode** (same tools, templated explanation) so nothing breaks.

## Why it satisfies Track 3
| Requirement | Where |
|---|---|
| AMD powers part of the working product | `app/agent.py` calls Token Factory for planning, explanations and PO rationale |
| Prediction must be explainable, not LLM-only | `app/tools/forecast.py`: seasonal-naive / moving average / exp. smoothing, chosen by backtest WAPE; every answer states method + WAPE |
| Measurable effect | `backtest/run_backtest.py`: 12-week replay vs a static min/max rule |
| Human approval | `app/store.py`: agent can only create `pending`; approve/reject need `X-Approver-Key`; no approve tool exists in the registry |

## Canonical data schema (adapter target for any other system)
`sales.csv(date,sku,units)` · `inventory.csv(sku,name,category,supplier_id,stock,on_order,unit_cost,unit_price,pack_size,moq,shelf_life_days,earliest_expiry_date)` · `suppliers.csv(supplier_id,name,lead_time_days,lead_time_std_days,min_order_value)`

## Policy (periodic review, protection interval L+R)
`safety = z·sqrt((L+R)σ² + (μσ_L)²)` · `S = demand(L+R) + safety` (capped at 80% of shelf life) · order when `position ≤ S − 0.5·demand(R)` · qty = `S − position` rounded to pack size and MOQ.

## Backtest results (sample data, seed 42) - read the caveats
See `backtest/results.json`. Caveats stated honestly: synthetic data; sales are used as demand; the baseline is a deliberately simple static rule; the copilot places more (smaller) orders; **forecast accuracy is about equal to a trailing mean on this data - the gain comes from safety-stock and pipeline-aware ordering, not from a better forecaster**. Re-run on real data before quoting numbers.

## Security notes
No keys in the repo (`.env` is git-ignored). Change `APPROVER_KEY` before any public deploy. Tool endpoints are unauthenticated by design for the demo.
# agentic-replenish
