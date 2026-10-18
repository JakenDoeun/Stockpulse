"""Engine, session dependency, shared column types and the database health probe."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import DateTime, TypeDecorator

from .config import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

# deterministic constraint names, so Alembic can alter them later (SQLite batch mode needs names)
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def utcnow() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC in and out on every backend (SQLite drops tzinfo on read)."""
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naive datetime: pass a timezone-aware UTC value.")
        return value.astimezone(UTC)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def make_engine(url: str) -> Engine:
    u = make_url(url)
    if u.get_backend_name() != "sqlite":
        return create_engine(url, pool_pre_ping=True)
    if u.database and u.database != ":memory:":
        Path(u.database).parent.mkdir(parents=True, exist_ok=True)
    eng = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enforce_foreign_keys(dbapi_conn, _record):  # SQLite ignores FKs unless asked per connection
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return eng


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database(eng: Engine | None = None) -> dict:
    """Connectivity plus migration state. Never includes the URL or credentials."""
    eng = eng or engine
    out = {"status": "ok", "backend": eng.dialect.name, "revision": None, "expected_revision": None, "detail": None}
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
            out["revision"] = MigrationContext.configure(conn).get_current_revision()
    except Exception as e:  # report, don't raise: /health must answer even when the DB is down
        return {**out, "status": "unavailable", "detail": type(e).__name__}
    out["expected_revision"] = ScriptDirectory(str(MIGRATIONS_DIR)).get_current_head()
    if out["revision"] != out["expected_revision"]:
        out["status"] = "migrations_pending"
    return out
