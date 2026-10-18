# StockPulse backend (Phase 1 foundation)

FastAPI + SQLAlchemy 2.0 + Alembic, serving the shared contract in [`../docs/api-contract.md`](../docs/api-contract.md).
Phase 1 provides the app shell, `/health`, the database schema and the contract schemas. Ingestion, forecasting,
optimization, LLM, PDF and dispatch arrive in later phases. The legacy engine in `../app/` keeps serving today's UI on :8000.

## Run locally (Python 3.12)

```bash
cd backend
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                                   # SQLite by default; edit for Postgres
.venv/bin/alembic upgrade head                         # create/upgrade the schema
.venv/bin/uvicorn app.main:app --reload --port 8001    # http://localhost:8001/health, /docs
```

`/health` returns `200 {"status": "ok", …}` when the database is reachable and migrated, otherwise `503` with
`database.status` set to `unavailable` or `migrations_pending`. It never includes the connection URL.

## Configuration (environment or `backend/.env`)

| Variable | Default | Notes |
|---|---|---|
| `APP_ENV` | `development` | `production` refuses SQLite and `CORS_ORIGINS=*` |
| `DATABASE_URL` | `sqlite:///./data/stockpulse.db` | Postgres: `postgresql+psycopg2://…`. Credentials only via env/secrets. |
| `CORS_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | Comma-separated; empty = same-origin only |

## Migrations

```bash
.venv/bin/alembic revision --autogenerate -m "describe change"   # then review the file: autogenerate is a draft
.venv/bin/alembic upgrade head
.venv/bin/alembic downgrade -1
```
`alembic.ini` contains no URL: `migrations/env.py` reads `DATABASE_URL` from the app settings.
In generated files, replace `app.db.UTCDateTime(...)` with `sa.DateTime(timezone=True)`.

## Tests

```bash
.venv/bin/python -m pytest -q                       # fresh temp SQLite database, deleted with the temp dir
TEST_DATABASE_URL=postgresql+psycopg2://user:pass@localhost:55432/stockpulse_test .venv/bin/python -m pytest -q
```
Tests never use `DATABASE_URL`. A `TEST_DATABASE_URL` whose database name doesn't end in `_test` is refused, and the
Postgres run downgrades to an empty schema at the end. A disposable Postgres:
`docker run -d --rm --name stockpulse-pg-test -e POSTGRES_USER=user -e POSTGRES_PASSWORD=pass -e POSTGRES_DB=stockpulse_test -p 127.0.0.1:55432:5432 postgres:16-alpine`.

## Layout

```
app/config.py        settings (pydantic-settings)
app/db.py            engine, session dependency (get_db), UTC datetime type, health probe
app/models.py        SQLAlchemy models (never returned to clients)
app/schemas.py       Pydantic API schemas = the shared contract; unknown fields are rejected
app/repositories.py  data access + DB-row → contract mapping
app/main.py          FastAPI app: lifespan, CORS, error envelope, /health
migrations/          Alembic (0001 = initial schema)
```

Errors always have the shape `{"detail": "<message>", "code": "<CODE>", "errors": [{"loc": [...], "message": "..."}]}`.
