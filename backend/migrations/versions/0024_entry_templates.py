"""Create entry_templates table for timesheet entry templates.

Revision ID: 0022
Revises: 0021
Create Date: 2026-06-06 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create entry_templates table."""
    op.create_table(
        "entry_templates",
        sa.Column("template_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("org_id", sa.Integer, nullable=False, server_default="1"),
        sa.Column("name", sa.String(100), nullable=False, comment="Template name e.g. 'Dev backend sprint'"),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.project_id"), nullable=True),
        sa.Column("task_type", sa.String(100), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("default_hours", sa.Numeric(5, 2), nullable=True, server_default="8.0"),
        sa.Column("is_favorite", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), onupdate=sa.func.now()),
    )

    # Index for frequent queries (employee_id lookup)
    op.create_index(
        "ix_entry_templates_employee_id",
        "entry_templates",
        ["employee_id"],
    )


def downgrade() -> None:
    """Drop entry_templates table."""
    op.drop_index("ix_entry_templates_employee_id", table_name="entry_templates")
    op.drop_table("entry_templates")
