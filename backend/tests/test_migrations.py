from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from conftest import run_alembic
from sqlalchemy import create_engine, inspect

from app import db as database


def test_migrations_match_the_models():
    with database.engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn, opts={"compare_type": True}), database.Base.metadata)
    assert diff == []


def test_upgrade_and_downgrade_on_a_fresh_database(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path}/fresh.db")
    run_alembic(eng, command.upgrade, "head")
    tables = set(inspect(eng).get_table_names())
    assert {"suppliers", "products", "sales_daily", "ingestion_batches", "supplier_updates", "purchase_orders",
            "purchase_order_items", "audit_events", "settings"} <= tables
    run_alembic(eng, command.downgrade, "base")
    assert set(inspect(eng).get_table_names()) == {"alembic_version"}
