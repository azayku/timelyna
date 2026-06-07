"""Add active_timers table for timer start/stop functionality.

Revision ID: 0021
Revises: 0020
Create Date: 2026-06-06 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create active_timers table."""
    op.create_table(
        "active_timers",
        sa.Column("timer_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("project_id", sa.BigInteger, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("org_id", sa.BigInteger, nullable=False, server_default="1"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("task_type", sa.String(100), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Index pour les requêtes fréquentes
    op.create_index(
        "ix_active_timers_employee_id",
        "active_timers",
        ["employee_id"],
    )


def downgrade() -> None:
    """Drop active_timers table."""
    op.drop_index("ix_active_timers_employee_id", table_name="active_timers")
    op.drop_table("active_timers")
