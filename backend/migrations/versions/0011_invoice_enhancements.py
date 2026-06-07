"""Invoice enhancements: due_date, paid_at, subtotal_ht, total_ttc + invoice_audit_logs.

Revision ID: 0011
Revises: 0010
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to invoices (idempotent — skip if already present)
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column("due_date", sa.Date, nullable=True))
        batch_op.add_column(sa.Column("subtotal_ht", sa.Numeric(12, 2), nullable=True))
        batch_op.add_column(sa.Column("total_ttc", sa.Numeric(12, 2), nullable=True))

    # Create invoice_line_items table
    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "invoice_id",
            sa.BigInteger,
            sa.ForeignKey("invoices.invoice_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False, server_default="1.00"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("skill_name", sa.String(100), nullable=True),
    )
    op.create_index("ix_invoice_line_items_invoice_id", "invoice_line_items", ["invoice_id"])

    # Create invoice_audit_logs table
    op.create_table(
        "invoice_audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "invoice_id",
            sa.BigInteger,
            sa.ForeignKey("invoices.invoice_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column(
            "performed_by",
            sa.BigInteger,
            sa.ForeignKey("employees.employee_id"),
            nullable=True,
        ),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_invoice_audit_logs_invoice_id", "invoice_audit_logs", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_invoice_audit_logs_invoice_id", table_name="invoice_audit_logs")
    op.drop_table("invoice_audit_logs")
    op.drop_index("ix_invoice_line_items_invoice_id", table_name="invoice_line_items")
    op.drop_table("invoice_line_items")
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_column("total_ttc")
        batch_op.drop_column("subtotal_ht")
        batch_op.drop_column("due_date")
