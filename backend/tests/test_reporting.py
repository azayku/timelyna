"""Tests for reporting & analytics (spec 04)."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.export import Export
from app.services.reporting_service import ReportingService

from tests.conftest import make_client, make_employee, make_entry, make_project


# ---------------------------------------------------------------------------
# 4.12 — Personal stats aggregation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_personal_stats_known_data(db: AsyncSession):
    """3 entries (2 billable, 1 not) → correct totals."""
    mgr = await make_employee(db, email="mgr_stats@example.com", role="manager")
    cli = await make_client(db, name="StatsClient")
    proj = await make_project(db, client_id=cli.client_id, manager_id=mgr.employee_id)
    emp = await make_employee(
        db, email="emp_stats@example.com", role="employee", manager_id=mgr.employee_id
    )

    today = date.today()
    # Entry 1: 4h billable, approved
    e1 = await make_entry(db, emp.employee_id, proj.project_id, today - timedelta(days=2), hours=4.0)
    from sqlalchemy import update
    from app.models.timesheet_entry import TimesheetEntry
    await db.execute(
        update(TimesheetEntry)
        .where(TimesheetEntry.timesheet_entry_id == e1.timesheet_entry_id)
        .values(status="approved", billable_flag=True)
    )

    # Entry 2: 6h billable, approved
    e2 = await make_entry(db, emp.employee_id, proj.project_id, today - timedelta(days=1), hours=6.0)
    await db.execute(
        update(TimesheetEntry)
        .where(TimesheetEntry.timesheet_entry_id == e2.timesheet_entry_id)
        .values(status="approved", billable_flag=True)
    )

    # Entry 3: 3h non-billable, draft
    e3 = await make_entry(db, emp.employee_id, proj.project_id, today, hours=3.0)
    await db.execute(
        update(TimesheetEntry)
        .where(TimesheetEntry.timesheet_entry_id == e3.timesheet_entry_id)
        .values(status="draft", billable_flag=False)
    )
    await db.commit()

    svc = ReportingService(db)
    result = await svc.get_personal_stats(emp.employee_id, period="all")

    assert result["total_hours"] == pytest.approx(13.0)
    assert result["billable_hours"] == pytest.approx(10.0)
    assert result["billable_pct"] == pytest.approx(76.9, abs=0.1)
    assert result["days_worked"] == 3


@pytest.mark.asyncio
async def test_personal_stats_empty(db: AsyncSession):
    """No entries → all zeros."""
    emp = await make_employee(db, email="emp_empty_stats@example.com", role="employee")

    svc = ReportingService(db)
    result = await svc.get_personal_stats(emp.employee_id, period="all")

    assert result["total_hours"] == 0.0
    assert result["billable_hours"] == 0.0
    assert result["billable_pct"] == 0.0
    assert result["days_worked"] == 0
    assert result["project_breakdown"] == []
    assert result["weekly_trend"] == []


# ---------------------------------------------------------------------------
# 4.13 — Financial margin / budget_warning
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_financial_report_budget_warning(db: AsyncSession):
    """Project with budget_hours=10, 9h actual → budget_warning=True (90% > 80%)."""
    mgr = await make_employee(db, email="mgr_fin1@example.com", role="manager")
    cli = await make_client(db, name="FinClient1")
    proj = await make_project(db, client_id=cli.client_id, manager_id=mgr.employee_id, name="BudgetWarnProj")

    # Set budget_hours = 10
    from sqlalchemy import update
    from app.models.project import Project
    await db.execute(
        update(Project)
        .where(Project.project_id == proj.project_id)
        .values(budget_hours=Decimal("10.00"))
    )

    emp = await make_employee(db, email="emp_fin1@example.com", role="employee", manager_id=mgr.employee_id)

    today = date.today()
    # 9 hours total across 2 entries, approved
    from app.models.timesheet_entry import TimesheetEntry
    e1 = await make_entry(db, emp.employee_id, proj.project_id, today - timedelta(days=1), hours=5.0)
    await db.execute(
        update(TimesheetEntry)
        .where(TimesheetEntry.timesheet_entry_id == e1.timesheet_entry_id)
        .values(status="approved")
    )
    e2 = await make_entry(db, emp.employee_id, proj.project_id, today, hours=4.0)
    await db.execute(
        update(TimesheetEntry)
        .where(TimesheetEntry.timesheet_entry_id == e2.timesheet_entry_id)
        .values(status="approved")
    )
    await db.commit()

    svc = ReportingService(db)
    result = await svc.get_financial_report(period="all", project_id=proj.project_id)

    assert len(result["projects"]) == 1
    project_row = result["projects"][0]
    assert project_row["actual_hours"] == pytest.approx(9.0)
    assert project_row["budget_warning"] is True


@pytest.mark.asyncio
async def test_financial_report_no_warning(db: AsyncSession):
    """Project with budget_hours=10, 7h actual → budget_warning=False (70% < 80%)."""
    mgr = await make_employee(db, email="mgr_fin2@example.com", role="manager")
    cli = await make_client(db, name="FinClient2")
    proj = await make_project(db, client_id=cli.client_id, manager_id=mgr.employee_id, name="NoWarnProj")

    from sqlalchemy import update
    from app.models.project import Project
    await db.execute(
        update(Project)
        .where(Project.project_id == proj.project_id)
        .values(budget_hours=Decimal("10.00"))
    )

    emp = await make_employee(db, email="emp_fin2@example.com", role="employee", manager_id=mgr.employee_id)

    today = date.today()
    from app.models.timesheet_entry import TimesheetEntry
    e1 = await make_entry(db, emp.employee_id, proj.project_id, today, hours=7.0)
    await db.execute(
        update(TimesheetEntry)
        .where(TimesheetEntry.timesheet_entry_id == e1.timesheet_entry_id)
        .values(status="approved")
    )
    await db.commit()

    svc = ReportingService(db)
    result = await svc.get_financial_report(period="all", project_id=proj.project_id)

    assert len(result["projects"]) == 1
    project_row = result["projects"][0]
    assert project_row["actual_hours"] == pytest.approx(7.0)
    assert project_row["budget_warning"] is False


# ---------------------------------------------------------------------------
# 4.14 — Integration test: export flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_flow(db: AsyncSession, client: AsyncClient):
    """POST /exports → get export_id, then process task, then GET download → URL."""
    emp = await make_employee(db, email="emp_export@example.com", role="employee")
    await db.commit()

    token = create_access_token({"sub": str(emp.employee_id), "employee_id": emp.employee_id, "role": "employee"})
    headers = {"Authorization": f"Bearer {token}"}

    # POST /exports
    resp = await client.post(
        "/api/v1/exports",
        json={"report_type": "personal_stats", "format": "csv", "filters": {}},
        headers=headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    export_id = data["export_id"]
    assert data["status"] == "pending"

    # Simulate task processing directly (no Celery in tests)
    from app.tasks.export_tasks import run_generate_export
    await run_generate_export(export_id, db)

    # GET /exports/{id}/download
    resp2 = await client.get(f"/api/v1/exports/{export_id}/download", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "download_url" in data2
    assert data2["download_url"].startswith("stub://")
