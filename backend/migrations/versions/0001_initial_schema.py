"""Initial schema - all tables.

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Employees ──────────────────────────────────────────────────────────
    op.create_table(
        "employees",
        sa.Column("employee_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="employee"),
        sa.Column("employment_status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("manager_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("org_id", sa.BigInteger, nullable=False, server_default="1"),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("hourly_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("hire_date", sa.Date, nullable=True),
        sa.Column("username", sa.String(50), nullable=True, unique=True),
        sa.Column("birth_date", sa.Date, nullable=True),
        sa.Column("must_change_password", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("deactivation_scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("annual_leave_days", sa.Integer, nullable=False, server_default="25"),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Refresh Tokens ─────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Login Attempts ─────────────────────────────────────────────────────
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("attempted_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Password Reset Tokens ──────────────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Absences ───────────────────────────────────────────────────────────
    op.create_table(
        "absences",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("absence_type", sa.String(50), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("approved_by", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Email Templates ────────────────────────────────────────────────────
    op.create_table(
        "email_templates",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("template_key", sa.String(100), nullable=False, unique=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("html_body", sa.Text, nullable=False),
        sa.Column("text_body", sa.Text, nullable=True),
        sa.Column("updated_by", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Notification Logs ──────────────────────────────────────────────────
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("reference_period", sa.String(20), nullable=True),
        sa.Column("email_address", sa.String(255), nullable=True),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Notification Preferences ───────────────────────────────────────────
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("in_app_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("employee_id", "type", name="uq_employee_notif_type"),
    )

    # ── Notifications ──────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.String(1000), nullable=True),
        sa.Column("related_entity_type", sa.String(50), nullable=True),
        sa.Column("related_entity_id", sa.BigInteger, nullable=True),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Clients ────────────────────────────────────────────────────────────
    op.create_table(
        "clients",
        sa.Column("client_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("default_billing_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("tax_id", sa.String(50), nullable=True),
        sa.Column("client_status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Organization Licenses ──────────────────────────────────────────────
    op.create_table(
        "organization_licenses",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(100), nullable=False, unique=True),
        sa.Column("license_token", sa.Text, nullable=False),
        sa.Column("pack", sa.String(50), nullable=True),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("grace_ends_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_validated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("validation_status", sa.String(50), nullable=False, server_default="valid"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Org Settings ───────────────────────────────────────────────────────
    op.create_table(
        "org_settings",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.BigInteger, nullable=False, unique=True, server_default="1"),
        sa.Column("standard_hours_per_day", sa.Numeric(5, 2), nullable=False, server_default="8.00"),
        sa.Column("max_hours_per_day", sa.Numeric(5, 2), nullable=False, server_default="24.00"),
        sa.Column("overtime_rate_multiplier", sa.Numeric(5, 2), nullable=False, server_default="1.25"),
        sa.Column("travel_rate_multiplier", sa.Numeric(5, 2), nullable=False, server_default="0.50"),
        sa.Column("default_currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("org_name", sa.String(255), nullable=False, server_default="Mon Organisation"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Skill Rates ────────────────────────────────────────────────────────
    op.create_table(
        "skill_rates",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.BigInteger, nullable=False, server_default="1"),
        sa.Column("skill_name", sa.String(100), nullable=False),
        sa.Column("billing_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "skill_name", name="uq_skill_rates_org_skill"),
    )

    # ── Projects ───────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("project_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.BigInteger, sa.ForeignKey("clients.client_id"), nullable=False),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("project_code", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("budget_hours", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("billing_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("manager_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("team_members", sa.JSON, nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Approvals ──────────────────────────────────────────────────────────
    op.create_table(
        "approvals",
        sa.Column("approval_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("manager_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("decided_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("employee_id", "week_start", name="uq_employee_week_start"),
    )

    # ── Exports ────────────────────────────────────────────────────────────
    op.create_table(
        "exports",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("s3_url", sa.String(500), nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Invoices ───────────────────────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("invoice_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.BigInteger, sa.ForeignKey("clients.client_id"), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False, unique=True),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("total_hours", sa.Numeric(10, 2), nullable=True),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="20.00"),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("line_items", sa.JSON, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("pdf_s3_url", sa.String(500), nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("paid_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # ── Timesheet Entries ──────────────────────────────────────────────────
    op.create_table(
        "timesheet_entries",
        sa.Column("timesheet_entry_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("project_id", sa.BigInteger, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("work_date", sa.Date, nullable=False),
        sa.Column("hours_worked", sa.Numeric(5, 2), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("entry_type", sa.String(50), nullable=False, server_default="normal"),
        sa.Column("billable_flag", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("billing_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("employee_id", "project_id", "work_date", "entry_type", name="uq_employee_project_date_type"),
    )

    # ── Project Team Members ───────────────────────────────────────────────
    op.create_table(
        "project_team_members",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.BigInteger, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("employee_id", sa.BigInteger, sa.ForeignKey("employees.employee_id"), nullable=False),
        sa.Column("skill_rate_id", sa.BigInteger, sa.ForeignKey("skill_rates.id"), nullable=True),
        sa.Column("custom_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("assigned_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "employee_id", name="uq_project_team_members"),
    )


def downgrade() -> None:
    op.drop_table("project_team_members")
    op.drop_table("timesheet_entries")
    op.drop_table("invoices")
    op.drop_table("exports")
    op.drop_table("approvals")
    op.drop_table("projects")
    op.drop_table("skill_rates")
    op.drop_table("org_settings")
    op.drop_table("organization_licenses")
    op.drop_table("clients")
    op.drop_table("notifications")
    op.drop_table("notification_preferences")
    op.drop_table("notification_logs")
    op.drop_table("email_templates")
    op.drop_table("absences")
    op.drop_table("password_reset_tokens")
    op.drop_table("login_attempts")
    op.drop_table("refresh_tokens")
    op.drop_table("employees")
