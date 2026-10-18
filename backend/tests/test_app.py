import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine

from app import db as database
from app.config import Settings
from app.main import app


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["app"]["environment"] == "test"
    assert body["database"] == {"status": "ok", "backend": database.engine.dialect.name, "revision": "0001",
                                "expected_revision": "0001", "detail": None}


def test_health_reports_unreachable_database(client, monkeypatch):
    monkeypatch.setattr(database, "engine", create_engine("sqlite:////nonexistent-dir/stockpulse.db"))
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["status"] == "degraded"
    assert r.json()["database"]["status"] == "unavailable"
    assert r.json()["database"]["detail"] == "OperationalError"
    assert "nonexistent-dir" not in r.text  # never leak the connection URL


def test_health_reports_pending_migrations(client, monkeypatch, tmp_path):
    monkeypatch.setattr(database, "engine", create_engine(f"sqlite:///{tmp_path}/empty.db"))
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["database"]["status"] == "migrations_pending"
    assert r.json()["database"]["revision"] is None


def test_startup_logs_and_shutdown_disposes_engine(monkeypatch, caplog):
    calls = []
    monkeypatch.setattr(database.engine, "dispose", lambda *a, **k: calls.append(1))
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        with TestClient(app):
            assert not calls
    assert calls == [1]
    assert any("starting StockPulse API" in m and "status=ok" in m for m in caplog.messages)


def test_cors_allows_only_configured_origins(client):
    pre = {"Access-Control-Request-Method": "GET"}
    ok = client.options("/health", headers={"Origin": "http://frontend.test", **pre})
    assert ok.headers.get("access-control-allow-origin") == "http://frontend.test"
    bad = client.options("/health", headers={"Origin": "http://evil.test", **pre})
    assert "access-control-allow-origin" not in bad.headers


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Not Found", "code": "NOT_FOUND", "errors": []}


def test_production_settings_guards():
    with pytest.raises(ValidationError, match="PostgreSQL"):
        Settings(app_env="production", database_url="sqlite:///./data/x.db")
    with pytest.raises(ValidationError, match="CORS"):
        Settings(app_env="production", database_url="postgresql+psycopg2://h/db", cors_origins="*")
    s = Settings(app_env="production", database_url="postgresql+psycopg2://h/db", cors_origins="https://a.example, https://b.example")
    assert s.cors_origin_list == ["https://a.example", "https://b.example"]
