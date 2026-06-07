"""Multi-org employee model: organizations, employee_skills, project_required_skills, employee_mutation_logs.

Revision ID: 0020
Revises: 0010
Create Date: 2024-02-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create organizations table ──────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("org_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("org_name", sa.String(255), nullable=False),
        sa.Column("manager_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # ── 2. Insert default organization row ─────────────────────────────────
    op.execute(
        """
        INSERT INTO organizations (org_id, org_name, manager_id, created_at, updated_at)
        VALUES (
            1,
            'Organisation par défaut',
            (SELECT employee_id FROM employees WHERE role = 'admin' ORDER BY employee_id LIMIT 1),
            now(),
            now()
        )
        """
    )

    # ── 3. Add FK constraint: employees.org_id → organizations.org_id ──────
    op.create_foreign_key(
        "fk_employees_org",
        "employees",
        "organizations",
        ["org_id"],
        ["org_id"],
    )

    # ── 4. Create employee_skills table ────────────────────────────────────
    op.create_table(
        "employee_skills",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("skill_rate_id", sa.BigInteger, sa.ForeignKey("skill_rates.id"), nullable=False),
        sa.Column("assigned_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("employee_id", "skill_rate_id", name="uq_employee_skills"),
    )

    # ── 5. Create project_required_skills table ────────────────────────────
    op.create_table(
        "project_required_skills",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.BigInteger, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("skill_rate_id", sa.BigInteger, sa.ForeignKey("skill_rates.id"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("project_id", "skill_rate_id", name="uq_project_required_skills"),
    )

    # ── 6. Create employee_mutation_logs table ─────────────────────────────
    op.create_table(
        "employee_mutation_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("from_org_id", sa.BigInteger, nullable=False),
        sa.Column("to_org_id", sa.BigInteger, nullable=False),
        sa.Column("mutated_by", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("mutated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("reason", sa.String(500), nullable=True),
    )

    # ── 7. Add nullable organizations_ref column to org_settings ──────────
    op.add_column(
        "org_settings",
        sa.Column("organizations_ref", sa.BigInteger, sa.ForeignKey("organizations.org_id"), nullable=True),
    )


def downgrade() -> None:
    # Reverse order

    # ── 7. Drop organizations_ref from org_settings ────────────────────────
    op.drop_column("org_settings", "organizations_ref")

    # ── 6. Drop employee_mutation_logs ─────────────────────────────────────
    op.drop_table("employee_mutation_logs")

    # ── 5. Drop project_required_skills ───────────────────────────────────
    op.drop_table("project_required_skills")

    # ── 4. Drop employee_skills ────────────────────────────────────────────
    op.drop_table("employee_skills")

    # ── 3. Drop FK constraint: employees.org_id → organizations.org_id ─────
    op.drop_constraint("fk_employees_org", "employees", type_="foreignkey")

    # ── 1. Drop organizations (also removes the default row) ───────────────
    op.drop_table("organizations")
