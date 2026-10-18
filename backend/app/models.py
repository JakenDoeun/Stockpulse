"""Database models. API shapes live in schemas.py; nothing here is returned to clients directly.

Names follow the shared contract (sku_id, supplier_id as int, supplier_updates).
Current inventory lives on Product (current_stock, on_order); daily closing stock, when the POS
export has it, lives on SalesDaily.stock_end. Derived values (PO total, line cost, approval time)
are computed, not stored, so they cannot disagree with their source rows.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, UTCDateTime, utcnow

Money = Numeric(12, 4)  # unit costs carry 4 dp (contract); totals are rounded to cents when computed
CENT = Decimal("0.01")


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Supplier(Timestamped, Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    email: Mapped[str | None] = mapped_column(String(254))


class Product(Timestamped, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("unit_cost >= 0", name="unit_cost_nonneg"),
        CheckConstraint("retail_price >= 0", name="retail_price_nonneg"),
        CheckConstraint("current_stock >= 0", name="current_stock_nonneg"),
        CheckConstraint("on_order >= 0", name="on_order_nonneg"),
        CheckConstraint("moq >= 1", name="moq_min"),
        CheckConstraint("pack_size >= 1", name="pack_size_min"),
        CheckConstraint("lead_time_days >= 1", name="lead_time_min"),
        CheckConstraint("max_stock IS NULL OR max_stock > 0", name="max_stock_pos"),
    )
    sku_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(80), default="")
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    unit_cost: Mapped[Decimal] = mapped_column(Money)
    retail_price: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    on_order: Mapped[int] = mapped_column(Integer, default=0)
    moq: Mapped[int] = mapped_column(Integer, default=1)
    pack_size: Mapped[int] = mapped_column(Integer, default=1)
    lead_time_days: Mapped[int] = mapped_column(Integer)  # no default: ingestion must supply or reject
    max_stock: Mapped[int | None] = mapped_column(Integer)

    supplier: Mapped[Supplier | None] = relationship()


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"
    __table_args__ = (
        CheckConstraint("kind IN ('products_csv','sales_csv','supplier_doc')", name="kind"),
        CheckConstraint("status IN ('received','processing','completed','failed')", name="status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default="received")
    row_count: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class SalesDaily(Base):
    __tablename__ = "sales_daily"
    __table_args__ = (
        UniqueConstraint("sku_id", "day"),
        CheckConstraint("units_sold >= 0", name="units_sold_nonneg"),
        CheckConstraint("units_normalized >= 0", name="units_normalized_nonneg"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku_id: Mapped[str] = mapped_column(ForeignKey("products.sku_id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date, index=True)
    units_sold: Mapped[float] = mapped_column(Float)
    units_normalized: Mapped[float] = mapped_column(Float)  # censored-demand normalizer output (stockout days imputed)
    stock_end: Mapped[float | None] = mapped_column(Float)
    censored: Mapped[bool] = mapped_column(Boolean, default=False)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_batches.id", ondelete="SET NULL"), index=True)


class SupplierUpdate(Base):
    """A supplier constraint read from a document (API: supplier_constraints[]); source_doc = batch.filename."""
    __tablename__ = "supplier_updates"
    __table_args__ = (
        CheckConstraint("new_cost IS NULL OR new_cost >= 0", name="new_cost_nonneg"),
        CheckConstraint("lead_time_days IS NULL OR lead_time_days >= 1", name="lead_time_min"),
        CheckConstraint("moq IS NULL OR moq >= 1", name="moq_min"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku_id: Mapped[str] = mapped_column(ForeignKey("products.sku_id", ondelete="CASCADE"), index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("ingestion_batches.id", ondelete="RESTRICT"), index=True)
    old_cost: Mapped[Decimal | None] = mapped_column(Money)
    new_cost: Mapped[Decimal | None] = mapped_column(Money)
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    moq: Mapped[int | None] = mapped_column(Integer)
    effective_date: Mapped[date | None] = mapped_column(Date)
    extraction_method: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    batch: Mapped[IngestionBatch] = relationship()


class PurchaseOrder(Timestamped, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (CheckConstraint("status IN ('draft','sent','failed')", name="status"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_number: Mapped[str] = mapped_column(String(40), unique=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    # snapshots of what the document was addressed to; the supplier record may change later
    supplier_name: Mapped[str] = mapped_column(String(120))
    supplier_email: Mapped[str | None] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    briefing: Mapped[str] = mapped_column(Text, default="")
    pdf_path: Mapped[str | None] = mapped_column(String(300))

    items: Mapped[list[PurchaseOrderItem]] = relationship(back_populates="purchase_order", cascade="all, delete-orphan",
                                                          order_by="PurchaseOrderItem.id")
    events: Mapped[list[AuditEvent]] = relationship(back_populates="purchase_order", cascade="all, delete-orphan",
                                                    order_by="AuditEvent.id")

    @property
    def total(self) -> Decimal:
        return sum((i.line_cost for i in self.items), Decimal("0.00"))


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", "sku_id"),
        CheckConstraint("quantity > 0", name="quantity_pos"),
        CheckConstraint("unit_cost >= 0", name="unit_cost_nonneg"),
        CheckConstraint("pack_size >= 1", name="pack_size_min"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    sku_id: Mapped[str] = mapped_column(ForeignKey("products.sku_id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)  # API: lines[].recommended_qty
    unit_cost: Mapped[Decimal] = mapped_column(Money)  # price at order time, not the live catalog price
    pack_size: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text, default="")

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

    @property
    def line_cost(self) -> Decimal:
        return (Decimal(self.quantity) * self.unit_cost).quantize(CENT, rounding=ROUND_HALF_UP)


class AuditEvent(Base):
    """Append-only history of a purchase order: creation, approval and each dispatch attempt."""
    __tablename__ = "audit_events"
    __table_args__ = (CheckConstraint("action IN ('created','approved','dispatch')", name="action"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(20))
    actor: Mapped[str | None] = mapped_column(String(120))
    channel: Mapped[str | None] = mapped_column(String(40))  # dispatch only: evolus_webhook | smtp | dry_run_outbox
    ok: Mapped[bool | None] = mapped_column(Boolean)  # dispatch only
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="events")


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
