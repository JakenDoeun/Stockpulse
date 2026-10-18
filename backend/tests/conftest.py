"""Tests only ever touch a throwaway database.

Default: a fresh SQLite file in a new temp directory. To run on PostgreSQL set TEST_DATABASE_URL;
its database name must end in `_test`, otherwise the run refuses to start.
"""
import os
import tempfile
from pathlib import Path

from sqlalchemy.engine import make_url

_url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tempfile.mkdtemp(prefix='stockpulse-test-')}/test.db"
_db_name = make_url(_url).database or ""
if not (Path(_db_name).name == "test.db" and "stockpulse-test-" in _db_name or _db_name.endswith("_test")):
    raise RuntimeError(f"Refusing to run tests against database '{_db_name}': use a temp SQLite file or a *_test database.")
# set before importing the app: settings and the engine are created at import time (env beats .env)
os.environ.update(DATABASE_URL=_url, APP_ENV="test", CORS_ORIGINS="http://frontend.test")

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db as database  # noqa: E402
from app.main import app  # noqa: E402

BACKEND = Path(__file__).resolve().parent.parent
FIXTURES = BACKEND.parent / "frontend" / "fixtures"


def run_alembic(engine, fn, revision: str) -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        fn(cfg, revision)


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    run_alembic(database.engine, command.upgrade, "head")
    yield
    run_alembic(database.engine, command.downgrade, "base")


@pytest.fixture
def session():
    s = database.SessionLocal()
    yield s
    s.rollback()
    s.close()
    with database.engine.begin() as conn:  # leave the schema, empty the tables
        for table in reversed(database.Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
