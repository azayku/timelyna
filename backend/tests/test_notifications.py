"""Tests for spec 10 — Notifications."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification
from app.models.timesheet_entry import TimesheetEntry
from app.tasks.notification_tasks import run_check_budget_warnings
from app.services.approval_service import ApprovalService
from app.services.timesheet_service import TimesheetService

from tests.conftest import make_employee, make_client, make_project, make_entry


# ---------------------------------------------------------------------------
# 10.9 — Budget warning thresholds
# ---------------------------------------------------------------------------

async def _setup_project_with_hours(db: AsyncSession, hours: float) -> dict:
    """Create a project with budget_hours=10 and approved entries totalling `hours`."""
    manager = await make_employee(
        db,
        email=f"mgr_{hours}@example.com",
        role="manager",
    )
    client = await make_client(db, name=f"Client_{hours}")
    project = await make_project(db, client_id=client.client_id, manager_id=manager.employee_id)

    # Set budget_hours = 10
    project.budget_hours = Decimal("10.00")
    await db.flush()

    employee = await make_employee(
        db,
        email=f"emp_{hours}@example.com",
        role="employee",
        manager_id=manager.employee_id,
    )

    if hours > 0:
        entry = await make_entry(
            db,
            employee_id=employee.employee_id,
            project_id=project.project_id,
            work_date=date(2025, 1, 6),
            hours=hours,
        )
        # Mark as approved so the query counts it
        entry.status = "approved"
        await db.flush()

    await db.commit()
    return {"project_id": project.project_id, "manager_id": manager.employee_id}


@pytest.mark.asyncio
async def test_budget_warning_79pct(db: AsyncSession):
    """79% of budget (7.9h / 10h) → NOT in warnings."""
    info = await _setup_project_with_hours(db, 7.9)
    warnings = await run_check_budget_warnings(db)
    project_ids = [w["project_id"] for w in warnings]
    assert info["project_id"] not in project_ids


@pytest.mark.asyncio
async def test_budget_warning_80pct(db: AsyncSession):
    """80% of budget (8.0h / 10h) → in warnings with level='warning'."""
    info = await _setup_project_with_hours(db, 8.0)
    warnings = await run_check_budget_warnings(db)
    match = next((w for w in warnings if w["project_id"] == info["project_id"]), None)
    assert match is not None, "Expected a warning at 80%"
    assert match["level"] == "warning"
    assert match["pct"] == 80.0


@pytest.mark.asyncio
async def test_budget_warning_100pct(db: AsyncSession):
    """100% of budget (10.0h / 10h) → in warnings with level='critical'."""
    info = await _setup_project_with_hours(db, 10.0)
    warnings = await run_check_budget_warnings(db)
    match = next((w for w in warnings if w["project_id"] == info["project_id"]), None)
    assert match is not None, "Expected a warning at 100%"
    assert match["level"] == "critical"
    assert match["pct"] == 100.0


# ---------------------------------------------------------------------------
# 10.10 — Integration: approve → notification created
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_creates_notification(db: AsyncSession):
    """Approving a timesheet creates an in-app notification for the employee."""
    # Setup: manager and employee
    manager = await make_employee(
        db,
        email="mgr_notif@example.com",
        role="manager",
    )
    employee = await make_employee(
        db,
        email="emp_notif@example.com",
        role="employee",
        manager_id=manager.employee_id,
    )
    client = await make_client(db, name="NotifClient")
    project = await make_project(
        db,
        client_id=client.client_id,
        manager_id=manager.employee_id,
    )

    # Create a draft entry
    await make_entry(
        db,
        employee_id=employee.employee_id,
        project_id=project.project_id,
        work_date=date(2025, 1, 6),
        hours=8.0,
    )
    await db.commit()

    # Submit the week
    ts_svc = TimesheetService(db)
    result = await ts_svc.submit_week(employee.employee_id, "2025-W02")
    approval_id = result["approval_id"]

    # Manager approves
    approval_svc = ApprovalService(db)
    await approval_svc.approve(
        approver_id=manager.employee_id,
        approval_id=approval_id,
    )

    # Verify notification was created for the employee
    notif_result = await db.execute(
        select(Notification).where(
            Notification.employee_id == employee.employee_id,
            Notification.type == "approval_approved",
        )
    )
    notification = notif_result.scalar_one_or_none()
    assert notification is not None, "Expected an approval_approved notification for the employee"
    assert notification.related_entity_type == "approval"
    assert notification.related_entity_id == approval_id
