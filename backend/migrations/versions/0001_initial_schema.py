"""Initial schema: suppliers, products, sales history, ingestion batches, supplier updates,
purchase orders + items, audit events, settings.

Revision ID: 0001
Revises: 
Create Date: 2026-10-18 14:28:20.853870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('ingestion_batches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("kind IN ('products_csv','sales_csv','supplier_doc')", name=op.f('ck_ingestion_batches_kind')),
    sa.CheckConstraint("status IN ('received','processing','completed','failed')", name=op.f('ck_ingestion_batches_status')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ingestion_batches'))
    )
    with op.batch_alter_table('ingestion_batches', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ingestion_batches_sha256'), ['sha256'], unique=False)

    op.create_table('settings',
    sa.Column('key', sa.String(length=60), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('key', name=op.f('pk_settings'))
    )
    op.create_table('suppliers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_suppliers')),
    sa.UniqueConstraint('name', name=op.f('uq_suppliers_name'))
    )
    op.create_table('products',
    sa.Column('sku_id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('category', sa.String(length=80), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('retail_price', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('current_stock', sa.Integer(), nullable=False),
    sa.Column('on_order', sa.Integer(), nullable=False),
    sa.Column('moq', sa.Integer(), nullable=False),
    sa.Column('pack_size', sa.Integer(), nullable=False),
    sa.Column('lead_time_days', sa.Integer(), nullable=False),
    sa.Column('max_stock', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('current_stock >= 0', name=op.f('ck_products_current_stock_nonneg')),
    sa.CheckConstraint('lead_time_days >= 1', name=op.f('ck_products_lead_time_min')),
    sa.CheckConstraint('max_stock IS NULL OR max_stock > 0', name=op.f('ck_products_max_stock_pos')),
    sa.CheckConstraint('moq >= 1', name=op.f('ck_products_moq_min')),
    sa.CheckConstraint('on_order >= 0', name=op.f('ck_products_on_order_nonneg')),
    sa.CheckConstraint('pack_size >= 1', name=op.f('ck_products_pack_size_min')),
    sa.CheckConstraint('retail_price >= 0', name=op.f('ck_products_retail_price_nonneg')),
    sa.CheckConstraint('unit_cost >= 0', name=op.f('ck_products_unit_cost_nonneg')),
    sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name=op.f('fk_products_supplier_id_suppliers'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('sku_id', name=op.f('pk_products'))
    )
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_products_supplier_id'), ['supplier_id'], unique=False)

    op.create_table('purchase_orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('po_number', sa.String(length=40), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=True),
    sa.Column('supplier_name', sa.String(length=120), nullable=False),
    sa.Column('supplier_email', sa.String(length=254), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('briefing', sa.Text(), nullable=False),
    sa.Column('pdf_path', sa.String(length=300), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('draft','sent','failed')", name=op.f('ck_purchase_orders_status')),
    sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name=op.f('fk_purchase_orders_supplier_id_suppliers'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_purchase_orders')),
    sa.UniqueConstraint('po_number', name=op.f('uq_purchase_orders_po_number'))
    )
    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_purchase_orders_supplier_id'), ['supplier_id'], unique=False)

    op.create_table('audit_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('purchase_order_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=20), nullable=False),
    sa.Column('actor', sa.String(length=120), nullable=True),
    sa.Column('channel', sa.String(length=40), nullable=True),
    sa.Column('ok', sa.Boolean(), nullable=True),
    sa.Column('detail', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("action IN ('created','approved','dispatch')", name=op.f('ck_audit_events_action')),
    sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name=op.f('fk_audit_events_purchase_order_id_purchase_orders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_events'))
    )
    with op.batch_alter_table('audit_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_audit_events_purchase_order_id'), ['purchase_order_id'], unique=False)

    op.create_table('purchase_order_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('purchase_order_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.String(length=64), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('pack_size', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.CheckConstraint('pack_size >= 1', name=op.f('ck_purchase_order_items_pack_size_min')),
    sa.CheckConstraint('quantity > 0', name=op.f('ck_purchase_order_items_quantity_pos')),
    sa.CheckConstraint('unit_cost >= 0', name=op.f('ck_purchase_order_items_unit_cost_nonneg')),
    sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name=op.f('fk_purchase_order_items_purchase_order_id_purchase_orders'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sku_id'], ['products.sku_id'], name=op.f('fk_purchase_order_items_sku_id_products'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_purchase_order_items')),
    sa.UniqueConstraint('purchase_order_id', 'sku_id', name=op.f('uq_purchase_order_items_purchase_order_id_sku_id'))
    )
    with op.batch_alter_table('purchase_order_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_purchase_order_items_purchase_order_id'), ['purchase_order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_purchase_order_items_sku_id'), ['sku_id'], unique=False)

    op.create_table('sales_daily',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.String(length=64), nullable=False),
    sa.Column('day', sa.Date(), nullable=False),
    sa.Column('units_sold', sa.Float(), nullable=False),
    sa.Column('units_normalized', sa.Float(), nullable=False),
    sa.Column('stock_end', sa.Float(), nullable=True),
    sa.Column('censored', sa.Boolean(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=True),
    sa.CheckConstraint('units_normalized >= 0', name=op.f('ck_sales_daily_units_normalized_nonneg')),
    sa.CheckConstraint('units_sold >= 0', name=op.f('ck_sales_daily_units_sold_nonneg')),
    sa.ForeignKeyConstraint(['batch_id'], ['ingestion_batches.id'], name=op.f('fk_sales_daily_batch_id_ingestion_batches'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['sku_id'], ['products.sku_id'], name=op.f('fk_sales_daily_sku_id_products'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sales_daily')),
    sa.UniqueConstraint('sku_id', 'day', name=op.f('uq_sales_daily_sku_id_day'))
    )
    with op.batch_alter_table('sales_daily', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sales_daily_batch_id'), ['batch_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_sales_daily_day'), ['day'], unique=False)

    op.create_table('supplier_updates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.String(length=64), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('old_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('new_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('lead_time_days', sa.Integer(), nullable=True),
    sa.Column('moq', sa.Integer(), nullable=True),
    sa.Column('effective_date', sa.Date(), nullable=True),
    sa.Column('extraction_method', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('lead_time_days IS NULL OR lead_time_days >= 1', name=op.f('ck_supplier_updates_lead_time_min')),
    sa.CheckConstraint('moq IS NULL OR moq >= 1', name=op.f('ck_supplier_updates_moq_min')),
    sa.CheckConstraint('new_cost IS NULL OR new_cost >= 0', name=op.f('ck_supplier_updates_new_cost_nonneg')),
    sa.ForeignKeyConstraint(['batch_id'], ['ingestion_batches.id'], name=op.f('fk_supplier_updates_batch_id_ingestion_batches'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['sku_id'], ['products.sku_id'], name=op.f('fk_supplier_updates_sku_id_products'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_supplier_updates'))
    )
    with op.batch_alter_table('supplier_updates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_supplier_updates_batch_id'), ['batch_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supplier_updates_sku_id'), ['sku_id'], unique=False)



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('supplier_updates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_supplier_updates_sku_id'))
        batch_op.drop_index(batch_op.f('ix_supplier_updates_batch_id'))

    op.drop_table('supplier_updates')
    with op.batch_alter_table('sales_daily', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sales_daily_day'))
        batch_op.drop_index(batch_op.f('ix_sales_daily_batch_id'))

    op.drop_table('sales_daily')
    with op.batch_alter_table('purchase_order_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_purchase_order_items_sku_id'))
        batch_op.drop_index(batch_op.f('ix_purchase_order_items_purchase_order_id'))

    op.drop_table('purchase_order_items')
    with op.batch_alter_table('audit_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_audit_events_purchase_order_id'))

    op.drop_table('audit_events')
    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_purchase_orders_supplier_id'))

    op.drop_table('purchase_orders')
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_products_supplier_id'))

    op.drop_table('products')
    op.drop_table('suppliers')
    op.drop_table('settings')
    with op.batch_alter_table('ingestion_batches', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ingestion_batches_sha256'))

    op.drop_table('ingestion_batches')
