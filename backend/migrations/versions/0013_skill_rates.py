"""Create skill_rates and project_team_members tables.

Revision ID: 0013
Revises: 0012
Create Date: 2025-01-01 00:01:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # skill_rates — may already exist from spec 11
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "skill_rates" not in existing_tables:
        op.create_table(
            "skill_rates",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("org_id", sa.Integer, nullable=False, server_default="1"),
            sa.Column("skill_name", sa.String(100), nullable=False),
            sa.Column("billing_rate", sa.Numeric(10, 2), nullable=False),
            sa.Column("description", sa.String(500), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint("org_id", "skill_name", name="uq_skill_rates_org_skill"),
        )

    if "project_team_members" not in existing_tables:
        op.create_table(
            "project_team_members",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "project_id",
                sa.Integer,
                sa.ForeignKey("projects.project_id"),
                nullable=False,
            ),
            sa.Column(
                "employee_id",
                sa.Integer,
                sa.ForeignKey("employees.employee_id"),
                nullable=False,
            ),
            sa.Column(
                "skill_rate_id",
                sa.Integer,
                sa.ForeignKey("skill_rates.id"),
                nullable=True,
            ),
            sa.Column("custom_rate", sa.Numeric(10, 2), nullable=True),
            sa.Column(
                "assigned_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint(
                "project_id", "employee_id", name="uq_project_team_members"
            ),
        )


def downgrade() -> None:
    op.drop_table("project_team_members")
    op.drop_table("skill_rates")
