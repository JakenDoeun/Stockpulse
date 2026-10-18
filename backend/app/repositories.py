"""Data access used by later phases. Functions take a Session and flush; the caller owns the commit."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .db import utcnow


def get_or_create_supplier(db: Session, name: str, email: str | None = None) -> models.Supplier:
    sup = db.scalar(select(models.Supplier).where(models.Supplier.name == name))
    if sup is None:
        sup = models.Supplier(name=name, email=email)
        db.add(sup)
    elif email:
        sup.email = email
    db.flush()
    return sup


def upsert_product(db: Session, sku_id: str, **fields) -> models.Product:
    p = db.get(models.Product, sku_id)
    if p is None:
        p = models.Product(sku_id=sku_id, **fields)
        db.add(p)
    else:
        for k, v in fields.items():
            setattr(p, k, v)
    db.flush()
    return p


def start_batch(db: Session, kind: str, filename: str, sha256: str) -> models.IngestionBatch:
    b = models.IngestionBatch(kind=kind, filename=filename, sha256=sha256, status="processing")
    db.add(b)
    db.flush()
    return b


def finish_batch(db: Session, batch: models.IngestionBatch, row_count: int | None = None, error: str | None = None) -> None:
    batch.status = "failed" if error else "completed"
    batch.row_count, batch.error, batch.completed_at = row_count, error, utcnow()
    db.flush()


def add_sales(db: Session, rows: list[dict], batch: models.IngestionBatch | None = None) -> int:
    """rows: {sku_id, day, units_sold, units_normalized, stock_end?, censored?}. (sku_id, day) must be new."""
    db.add_all(models.SalesDaily(batch_id=batch.id if batch else None, **r) for r in rows)
    db.flush()
    return len(rows)


def create_purchase_order(db: Session, supplier: models.Supplier | None, lines: list[dict],
                          briefing: str = "", actor: str | None = None) -> models.PurchaseOrder:
    """lines: {sku_id, quantity, unit_cost: Decimal, pack_size, reason}. Records a 'created' audit event."""
    po = models.PurchaseOrder(po_number=f"tmp-{uuid4().hex}", supplier_id=supplier.id if supplier else None,
                              supplier_name=supplier.name if supplier else "Unassigned supplier",
                              supplier_email=supplier.email if supplier else None, briefing=briefing,
                              items=[models.PurchaseOrderItem(**ln) for ln in lines])
    db.add(po)
    db.flush()  # assigns id, used for a collision-free number
    po.po_number = f"PO-{po.created_at:%Y%m%d}-{po.id:03d}"
    record_event(db, po, "created", actor=actor)
    return po


def record_event(db: Session, po: models.PurchaseOrder, action: str, actor: str | None = None,
                 channel: str | None = None, ok: bool | None = None, detail: str = "") -> models.AuditEvent:
    ev = models.AuditEvent(action=action, actor=actor, channel=channel, ok=ok, detail=detail)
    po.events.append(ev)
    db.flush()
    return ev


def purchase_order_out(po: models.PurchaseOrder) -> schemas.PurchaseOrderOut:
    """DB row -> contract shape. Dispatch fields summarise the latest approval's dispatch attempts."""
    approvals = [e for e in po.events if e.action == "approved"]
    last_approval = approvals[-1] if approvals else None
    sends = [e for e in po.events if e.action == "dispatch" and last_approval and e.id > last_approval.id]
    return schemas.PurchaseOrderOut(
        id=po.id, po_number=po.po_number, supplier=po.supplier_name, supplier_email=po.supplier_email or "",
        status=po.status, total=float(po.total),
        lines=[schemas.POLine(sku_id=i.sku_id, name=i.product.name, recommended_qty=i.quantity, unit_cost=float(i.unit_cost),
                              line_cost=float(i.line_cost), pack_size=i.pack_size, reason=i.reason) for i in po.items],
        pdf_url=f"/api/po/{po.id}/pdf",
        dispatch_channel=",".join(e.channel or "" for e in sends),
        dispatch_detail=" | ".join(f"{e.channel}: {e.detail}" for e in sends),
        created_at=po.created_at, approved_at=last_approval.created_at if last_approval else None,
    )
