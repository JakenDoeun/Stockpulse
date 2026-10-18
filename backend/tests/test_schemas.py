import json

import pytest
from conftest import FIXTURES
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from app import schemas
from app.main import app


@pytest.mark.parametrize("fixture,model", [("dashboard.json", schemas.Dashboard), ("what_if_2500.json", schemas.Dashboard),
                                           ("po_draft.json", schemas.PODraftResponse)])
def test_frontend_fixtures_match_the_contract(fixture, model):
    model.model_validate(json.loads((FIXTURES / fixture).read_text()))


def test_undocumented_fields_are_rejected():
    d = json.loads((FIXTURES / "dashboard.json").read_text())
    d["kpis"]["new_metric"] = 1
    with pytest.raises(ValidationError, match="new_metric"):
        schemas.Dashboard.model_validate(d)


def test_what_if_is_history_free_and_defaults_match_contract():
    d = json.loads((FIXTURES / "what_if_2500.json").read_text())
    assert all(f.get("history") is None for f in d["forecasts"])
    assert schemas.WhatIfRequest().model_dump() == {"budget_cap": None, "lead_time_delta_days": 0, "lead_time_overrides": {},
                                                    "demand_multiplier": 1.0, "explain": False}


@pytest.mark.parametrize("body,field", [
    ({"budget_cap": -1}, "budget_cap"),
    ({"demand_multiplier": 0}, "demand_multiplier"),
    ({"lead_time_overrides": {"SKU-101": 0}}, "lead_time_overrides"),
    ({"lead_time_overrides": {"  ": 5}}, "lead_time_overrides"),
    ({"budgetCap": 100}, "budgetCap"),  # typo is rejected, not silently ignored
])
def test_what_if_rejects_invalid_input(body, field):
    with pytest.raises(ValidationError, match=field):
        schemas.WhatIfRequest.model_validate(body)


def test_po_requests_validate():
    with pytest.raises(ValidationError, match="quantity_overrides"):
        schemas.PODraftRequest.model_validate({"quantity_overrides": {"SKU-101": -5}})
    with pytest.raises(ValidationError, match="recipient_override"):
        schemas.ApproveRequest.model_validate({"recipient_override": "not-an-email"})
    assert schemas.ApproveRequest.model_validate({"recipient_override": " buyer@shop.example "}).recipient_override == "buyer@shop.example"


def test_risk_union_is_checked_per_type():
    risk = TypeAdapter(schemas.Risk)
    base = {"sku_id": "SKU-1", "name": "Cola", "severity": "high", "score": 80, "message": "m"}
    with pytest.raises(ValidationError):
        risk.validate_python({**base, "type": "stockout", "days_of_supply": 2})  # stockout fields missing
    with pytest.raises(ValidationError):
        risk.validate_python({**base, "type": "flood"})
    assert risk.validate_python({**base, "type": "dead_stock", "days_since_last_sale": 40, "capital_locked": 12.5}).type == "dead_stock"


@pytest.fixture(scope="module")
def probe_client():
    """Test-only routes to exercise the error handlers; removed afterwards."""
    router = APIRouter()

    @router.post("/_probe/what-if")
    def _what_if(body: schemas.WhatIfRequest):
        return body

    @router.get("/_probe/boom")
    def _boom():
        raise RuntimeError("secret internals")

    before = list(app.router.routes)
    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.router.routes[:] = before


def test_validation_error_envelope(probe_client):
    r = probe_client.post("/_probe/what-if", json={"budget_cap": -5, "demand_multiplier": 0})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_FAILED"
    assert body["detail"].startswith("Invalid budget_cap:") and body["detail"].endswith("(and 1 more)")
    assert [e["loc"] for e in body["errors"]] == [["body", "budget_cap"], ["body", "demand_multiplier"]]


def test_malformed_json_uses_envelope(probe_client):
    r = probe_client.post("/_probe/what-if", content=b"{not json", headers={"content-type": "application/json"})
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_FAILED"


def test_unexpected_error_hides_internals(probe_client):
    r = probe_client.get("/_probe/boom")
    assert r.status_code == 500
    assert r.json() == {"detail": "Internal server error.", "code": "INTERNAL_ERROR", "errors": []}
