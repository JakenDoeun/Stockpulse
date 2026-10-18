import re
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError, StatementError

from app import db as database
from app import models
from app import repositories as repo


def _catalog(s):
    sup = repo.get_or_create_supplier(s, "FreshCo", "orders@freshco.example")
    cola = repo.upsert_product(s, "SKU-101", name="Cola 330ml", supplier_id=sup.id, unit_cost=Decimal("0.1000"),
                               retail_price=Decimal("0.6000"), current_stock=40, pack_size=24, moq=24, lead_time_days=5)
    chips = repo.upsert_product(s, "SKU-102", name="Chips", supplier_id=sup.id, unit_cost=Decimal("1.3333"),
                                current_stock=0, lead_time_days=3)
    return sup, cola, chips


def test_supplier_and_product_upserts(session):
    sup, cola, _ = _catalog(session)
    assert repo.get_or_create_supplier(session, "FreshCo").id == sup.id
    repo.upsert_product(session, "SKU-101", current_stock=12)
    session.commit()
    assert session.get(models.Product, "SKU-101").current_stock == 12
    assert session.get(models.Product, "SKU-101").unit_cost == Decimal("0.1000")  # Numeric, not float


def test_check_constraints_reject_bad_rows(session):
    _catalog(session)
    with pytest.raises(IntegrityError):
        repo.upsert_product(session, "SKU-101", pack_size=0)


def test_sales_unique_per_day_and_foreign_keys_enforced(session):
    _catalog(session)
    batch = repo.start_batch(session, "sales_csv", "sales.csv", "a" * 64)
    row = dict(sku_id="SKU-101", day=date(2026, 10, 1), units_sold=5, units_normalized=5)
    assert repo.add_sales(session, [row], batch) == 1
    session.commit()
    with pytest.raises(IntegrityError):
        repo.add_sales(session, [row])
    session.rollback()
    with pytest.raises(IntegrityError):  # SQLite needs PRAGMA foreign_keys for this
        repo.add_sales(session, [{**row, "sku_id": "NO-SUCH-SKU"}])


def test_ingestion_batch_lifecycle(session):
    ok = repo.start_batch(session, "products_csv", "products.csv", "b" * 64)
    assert ok.status == "processing"
    repo.finish_batch(session, ok, row_count=10)
    bad = repo.start_batch(session, "supplier_doc", "notice.pdf", "c" * 64)
    repo.finish_batch(session, bad, error="Unreadable PDF")
    session.commit()
    session.expire_all()
    assert (ok.status, ok.row_count, ok.error) == ("completed", 10, None)
    assert (bad.status, bad.error) == ("failed", "Unreadable PDF")
    assert ok.completed_at.tzinfo is not None  # aware UTC after a round trip, on every backend


def test_purchase_order_totals_events_and_contract_mapping(session):
    sup, _, _ = _catalog(session)
    po = repo.create_purchase_order(session, sup, [
        dict(sku_id="SKU-101", quantity=3, unit_cost=Decimal("0.1000"), pack_size=1, reason="test"),
        dict(sku_id="SKU-102", quantity=7, unit_cost=Decimal("1.3333"), pack_size=1, reason="test"),
    ], briefing="b", actor="system")
    session.commit()
    assert re.fullmatch(r"PO-\d{8}-\d{3}", po.po_number)
    assert [i.line_cost for i in po.items] == [Decimal("0.30"), Decimal("9.33")]  # 3 x 0.1 is exact, unlike float
    assert po.total == Decimal("9.63")
    assert [e.action for e in po.events] == ["created"]

    out = repo.purchase_order_out(po)
    assert (out.status, out.total, out.supplier_email, out.approved_at, out.dispatch_channel) == ("draft", 9.63, "orders@freshco.example", None, "")
    assert out.lines[0].name == "Cola 330ml" and out.lines[0].recommended_qty == 3

    repo.record_event(session, po, "approved", actor="owner")
    repo.record_event(session, po, "dispatch", channel="smtp", ok=True, detail="sent to orders@freshco.example")
    session.commit()
    out = repo.purchase_order_out(po)
    assert out.approved_at is not None and out.approved_at.tzinfo == UTC
    assert (out.dispatch_channel, out.dispatch_detail) == ("smtp", "smtp: sent to orders@freshco.example")


def test_products_on_a_purchase_order_cannot_be_deleted(session):
    sup, cola, _ = _catalog(session)
    repo.create_purchase_order(session, sup, [dict(sku_id="SKU-101", quantity=24, unit_cost=Decimal("0.1"), pack_size=24)])
    session.commit()
    session.delete(cola)
    with pytest.raises(IntegrityError):
        session.flush()


def test_naive_datetimes_are_rejected(session):
    b = repo.start_batch(session, "sales_csv", "s.csv", "d" * 64)
    b.completed_at = datetime(2026, 10, 18, 9, 0)  # no tzinfo
    with pytest.raises(StatementError, match="Naive datetime"):
        session.flush()


def test_sessions_come_from_the_dependency():
    gen = database.get_db()
    s = next(gen)
    assert s.bind is database.engine
    gen.close()
