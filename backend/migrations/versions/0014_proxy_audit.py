"""0014 — proxy_audit_logs table + proxy_admin_id on timesheet_entries

Revision ID: 0014
Revises: 0013
Create Date: 2025-01-01 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "proxy_audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("admin_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entries_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("token_jti", sa.String(100), nullable=False, unique=True),
    )

    op.add_column(
        "timesheet_entries",
        sa.Column("proxy_admin_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("timesheet_entries", "proxy_admin_id")
    op.drop_table("proxy_audit_logs")
