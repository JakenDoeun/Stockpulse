"""API request/response schemas: the shared contract (docs/api-contract.md) in code.

Field names are the contract's; do not rename here without a CONTRACT.md change.
Every model forbids unknown fields, so undocumented additions fail tests instead of reaching clients.
Units: *_mape / *_pct are percent (0-100); budget_utilization and service levels are fractions (0-1).
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

SkuId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
Email = Annotated[str, StringConstraints(strip_whitespace=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
Severity = Literal["high", "medium", "low"]
RiskType = Literal["stockout", "margin_erosion", "dead_stock", "overstock"]
NonNeg = Annotated[float, Field(ge=0)]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- errors ---------------------------------------------------------------------------------
class FieldError(Schema):
    loc: list[str | int]
    message: str


class ErrorResponse(Schema):
    """Every non-2xx JSON body. `detail` is always a human-readable string."""
    detail: str
    code: str
    errors: list[FieldError] = []


# ---- health ---------------------------------------------------------------------------------
class AppInfo(Schema):
    name: str
    version: str
    environment: Literal["development", "test", "production"]


class DatabaseHealth(Schema):
    status: Literal["ok", "unavailable", "migrations_pending"]
    backend: str
    revision: str | None
    expected_revision: str | None
    detail: str | None


class HealthResponse(Schema):
    status: Literal["ok", "degraded"]
    app: AppInfo
    database: DatabaseHealth


# ---- dashboard (GET /api/dashboard, POST /api/what-if) ----------------------------------------
class Scenario(Schema):
    lead_time_delta_days: int
    lead_time_overrides: dict[SkuId, int]
    demand_multiplier: float


class Kpis(Schema):
    skus_tracked: int
    high_risk_count: int
    imminent_stockouts: int
    revenue_at_risk: float
    capital_locked_dead_stock: float
    avg_model_mape: float | None
    avg_baseline_mape: float | None
    avg_improvement_pct: float | None  # RMSE-based improvement vs baseline, percent
    cart_total: float
    budget_utilization: float


class SupplierConstraint(Schema):
    sku_id: SkuId
    name: str
    old_cost: float | None
    new_cost: float | None
    lead_time_days: int | None
    moq: int | None
    effective_date: date | None
    source_doc: str
    extraction_method: str  # "amd_vllm" | "rules" today; DS may add methods
    headline: str


class HistoryPoint(Schema):
    date: date
    units: float
    normalized: float


class ForecastPoint(Schema):
    date: date
    mean: NonNeg
    lower: NonNeg | None  # null when the model supplies no interval (C4)
    upper: NonNeg | None


class ForecastMetrics(Schema):
    model_mape: float | None
    baseline_mape: float | None
    model_rmse: float | None
    baseline_rmse: float | None
    improvement_pct: float | None
    holdout_days: int
    model: str
    baseline: str


class Forecast(Schema):
    sku_id: SkuId
    name: str
    daily_mean: NonNeg
    daily_std: NonNeg
    interval: str | None
    history: list[HistoryPoint] | None = None  # omitted in what-if
    forecast: list[ForecastPoint]
    metrics: ForecastMetrics
    method_note: str | None = None


class _RiskBase(Schema):
    sku_id: SkuId
    name: str
    severity: Severity
    score: Annotated[float, Field(ge=0, le=100)]
    message: str


class StockoutRisk(_RiskBase):
    type: Literal["stockout"]
    days_of_supply: float
    lead_time_days: int
    stockout_date: date
    daily_demand: float
    revenue_at_risk: float


class MarginErosionRisk(_RiskBase):
    type: Literal["margin_erosion"]
    margin_before_pct: float
    margin_after_pct: float
    old_cost: float
    new_cost: float
    suggested_retail_price: float | None


class DeadStockRisk(_RiskBase):
    type: Literal["dead_stock"]
    days_since_last_sale: int  # 999 = never sold
    capital_locked: float


class OverstockRisk(_RiskBase):
    type: Literal["overstock"]
    days_of_supply: float
    capital_locked: float


Risk = Annotated[StockoutRisk | MarginErosionRisk | DeadStockRisk | OverstockRisk, Field(discriminator="type")]


class _CartLineBase(Schema):
    sku_id: SkuId
    name: str
    supplier_id: int | None
    supplier_name: str
    unit_cost: NonNeg
    pack_size: Annotated[int, Field(ge=1)]
    moq: Annotated[int, Field(ge=0)]
    reorder_point: float
    safety_stock: float
    units_needed: int
    current_stock: int
    daily_demand: float
    lead_time_days: int
    risk: RiskType | Literal["none"]
    risk_severity: Severity | Literal["none"]
    recommended_qty: Annotated[int, Field(ge=0)]
    line_cost: NonNeg
    reason: str


class CartItem(_CartLineBase):
    packs: int
    expected_service_level: Annotated[float, Field(ge=0, le=1)]
    days_of_cover_after: float


class UnboughtLine(_CartLineBase):
    pass


class Cart(Schema):
    budget_cap: NonNeg
    total_cost: NonNeg
    budget_utilization: NonNeg
    unconstrained_cost: NonNeg
    solver_status: str
    avg_service_level: float | None
    items: list[CartItem]
    unbought: list[UnboughtLine]


class BaselineAccuracy(Schema):
    model_mape: float | None
    baseline_mape: float | None


class Telemetry(Schema):
    model: str
    endpoint_configured: bool
    endpoint_host: str | None
    hardware: str
    calls: int
    last_latency_s: float | None
    last_tokens_per_sec: float | None
    total_completion_tokens: int
    last_error: str | None
    engine_source: Literal["stockpulse_ds", "reference"]
    pipeline_compute_ms: int
    baseline_accuracy: BaselineAccuracy


class Dashboard(Schema):
    generated_at: datetime
    as_of: date
    budget_cap: NonNeg
    horizon_days: int
    scenario: Scenario
    kpis: Kpis
    supplier_constraints: list[SupplierConstraint]
    forecasts: list[Forecast]
    risks: list[Risk]
    cart: Cart
    telemetry: Telemetry
    briefing: str


class WhatIfRequest(Schema):
    budget_cap: Annotated[float, Field(ge=0)] | None = None
    lead_time_delta_days: Annotated[int, Field(ge=-365, le=365)] = 0
    lead_time_overrides: dict[SkuId, Annotated[int, Field(ge=1, le=365)]] = {}
    demand_multiplier: Annotated[float, Field(gt=0, le=10)] = 1.0
    explain: bool = False


# ---- ingest (POST /api/ingest, multipart; the response is JSON) ------------------------------
class SalesIngestSummary(Schema):
    rows: int
    skus: int
    censored_days: int
    date_min: date
    date_max: date


class SupplierDocIngestSummary(Schema):
    method: str
    skus: list[SkuId]
    count: int


class IngestResponse(Schema):
    products: int | None = None  # rows upserted
    sales: SalesIngestSummary | None = None
    supplier_updates: SupplierDocIngestSummary | None = None
    constraints: list[SupplierConstraint]


# ---- purchase orders ------------------------------------------------------------------------
class PODraftRequest(Schema):
    budget_cap: Annotated[float, Field(ge=0)] | None = None
    quantity_overrides: dict[SkuId, Annotated[int, Field(ge=0)]] = {}


class POLine(Schema):
    sku_id: SkuId
    name: str
    recommended_qty: Annotated[int, Field(ge=0)]
    unit_cost: NonNeg
    line_cost: NonNeg
    pack_size: Annotated[int, Field(ge=1)]
    reason: str


class PurchaseOrderOut(Schema):
    id: int
    po_number: str
    supplier: str
    supplier_email: str
    status: Literal["draft", "sent", "failed"]
    total: NonNeg
    lines: list[POLine]
    pdf_url: str
    dispatch_channel: str
    dispatch_detail: str
    created_at: datetime
    approved_at: datetime | None


class PODraftResponse(Schema):
    purchase_orders: list[PurchaseOrderOut]
    briefing: str


class ApproveRequest(Schema):
    recipient_override: Email | None = None


class DispatchChannelResult(Schema):
    channel: Literal["evolus_webhook", "smtp", "dry_run_outbox"]
    ok: bool
    detail: str


class DispatchResult(Schema):
    ok: bool
    results: list[DispatchChannelResult]


class ApproveResponse(PurchaseOrderOut):
    dispatch: DispatchResult
