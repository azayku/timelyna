"""Unit tests for ApprovalService — TEST-APP-001 through TEST-APP-009."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval
from app.models.organization import Organization
from app.models.timesheet_entry import TimesheetEntry
from app.services.approval_service import ApprovalService

from tests.unit.conftest import (
    _make_approval,
    _make_client,
    _make_employee,
    _make_entry,
    _make_org,
    _make_project,
)

PAST_DATE = date(2026, 5, 5)
WEEK_START = date(2026, 5, 4)  # Monday of W19


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_team(db: AsyncSession, manager_email: str, employee_email: str):
    """Create a manager + employee in the same org, return (manager, employee)."""
    manager = await _make_employee(
        db,
        email=manager_email,
        role="manager",
        first_name="Mgr",
        last_name="One",
    )
    # Manager is now set as org manager by _make_employee for role=="manager"
    employee = await _make_employee(
        db,
        email=employee_email,
        role="employee",
        manager_id=manager.employee_id,
        first_name="Emp",
        last_name="One",
    )
    return manager, employee


# ---------------------------------------------------------------------------
# TEST-APP-001 — approve pending approval success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_pending_approval_success(db: AsyncSession):
    manager, employee = await _setup_team(db, "app001mgr@test.com", "app001emp@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, manager.employee_id)

    # 2 submitted entries
    for d in [WEEK_START, WEEK_START + timedelta(days=1)]:
        entry = await _make_entry(db, employee.employee_id, project.project_id, d, hours=8.0, status="submitted")

    approval = await _make_approval(
        db,
        employee_id=employee.employee_id,
        manager_id=manager.employee_id,
        week_start=WEEK_START,
        status="pending",
    )
    await db.commit()

    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
            service = ApprovalService(db)
            result = await service.approve(
                approver_id=manager.employee_id,
                approval_id=approval.approval_id,
                notes="Looks good",
            )

    assert result["approval_id"] == approval.approval_id
    assert result["status"] == "approved"

    # Verify DB state
    res = await db.execute(select(Approval).where(Approval.approval_id == approval.approval_id))
    updated_approval = res.scalar_one()
    assert updated_approval.status == "approved"

    # All submitted entries should now be approved
    entries_res = await db.execute(
        select(TimesheetEntry).where(
            TimesheetEntry.employee_id == employee.employee_id,
            TimesheetEntry.work_date >= WEEK_START,
            TimesheetEntry.work_date <= WEEK_START + timedelta(days=6),
            TimesheetEntry.deleted_at.is_(None),
        )
    )
    entries = entries_res.scalars().all()
    for entry in entries:
        assert entry.status == "approved"
        assert entry.approved_at is not None


# ---------------------------------------------------------------------------
# TEST-APP-002 — approve already approved raises 409
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_already_approved_raises_409(db: AsyncSession):
    manager, employee = await _setup_team(db, "app002mgr@test.com", "app002emp@test.com")
    approval = await _make_approval(
        db,
        employee_id=employee.employee_id,
        manager_id=manager.employee_id,
        week_start=WEEK_START,
        status="approved",
    )
    await db.commit()

    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        service = ApprovalService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.approve(
                approver_id=manager.employee_id,
                approval_id=approval.approval_id,
            )

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# TEST-APP-003 — approve by unauthorized manager raises 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_by_unauthorized_manager_raises_403(db: AsyncSession):
    # org 1: manager_a + employee
    manager_a, employee = await _setup_team(db, "app003mgra@test.com", "app003emp@test.com")

    # org 2: unrelated manager_b
    org2 = await _make_org(db, org_id=2, manager_id=None)
    manager_b = await _make_employee(
        db,
        email="app003mgrb@test.com",
        role="manager",
        org_id=2,
        first_name="Mgr",
        last_name="Two",
    )

    approval = await _make_approval(
        db,
        employee_id=employee.employee_id,
        manager_id=manager_a.employee_id,
        week_start=WEEK_START,
        status="pending",
    )
    await db.commit()

    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        service = ApprovalService(db)
        with pytest.raises(HTTPException) as exc_info:
            # manager_b tries to approve employee from org 1
            await service.approve(
                approver_id=manager_b.employee_id,
                approval_id=approval.approval_id,
            )

    assert exc_info.value.status_code in (403, 404)


# ---------------------------------------------------------------------------
# TEST-APP-004 — reject approval with reason success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_approval_with_reason_success(db: AsyncSession):
    manager, employee = await _setup_team(db, "app004mgr@test.com", "app004emp@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, manager.employee_id)

    # 2 submitted entries
    for d in [WEEK_START, WEEK_START + timedelta(days=1)]:
        await _make_entry(db, employee.employee_id, project.project_id, d, hours=8.0, status="submitted")

    approval = await _make_approval(
        db,
        employee_id=employee.employee_id,
        manager_id=manager.employee_id,
        week_start=WEEK_START,
        status="pending",
    )
    await db.commit()

    reason = "Heures incorrectes sur le projet X"
    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
            service = ApprovalService(db)
            result = await service.reject(
                approver_id=manager.employee_id,
                approval_id=approval.approval_id,
                rejection_reason=reason,
            )

    assert result["status"] == "rejected"

    # Approval in DB
    res = await db.execute(select(Approval).where(Approval.approval_id == approval.approval_id))
    updated = res.scalar_one()
    assert updated.status == "rejected"
    assert updated.rejection_reason == reason

    # Entries should revert to draft
    entries_res = await db.execute(
        select(TimesheetEntry).where(
            TimesheetEntry.employee_id == employee.employee_id,
            TimesheetEntry.work_date >= WEEK_START,
            TimesheetEntry.work_date <= WEEK_START + timedelta(days=6),
            TimesheetEntry.deleted_at.is_(None),
        )
    )
    entries = entries_res.scalars().all()
    for entry in entries:
        assert entry.status == "draft"


# ---------------------------------------------------------------------------
# TEST-APP-005 — reject with short reason raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_approval_reason_too_short_raises_422(db: AsyncSession):
    manager, employee = await _setup_team(db, "app005mgr@test.com", "app005emp@test.com")
    approval = await _make_approval(
        db,
        employee_id=employee.employee_id,
        manager_id=manager.employee_id,
        week_start=WEEK_START,
        status="pending",
    )
    await db.commit()

    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        service = ApprovalService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.reject(
                approver_id=manager.employee_id,
                approval_id=approval.approval_id,
                rejection_reason="Bad",  # < 10 characters
            )

    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# TEST-APP-006 — cancel own pending approval success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_own_pending_approval_success(db: AsyncSession):
    manager, employee = await _setup_team(db, "app006mgr@test.com", "app006emp@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, manager.employee_id)

    await _make_entry(db, employee.employee_id, project.project_id, WEEK_START, hours=8.0, status="submitted")

    approval = await _make_approval(
        db,
        employee_id=employee.employee_id,
        manager_id=manager.employee_id,
        week_start=WEEK_START,
        status="pending",
    )
    await db.commit()

    service = ApprovalService(db)
    result = await service.cancel(
        employee_id=employee.employee_id,
        approval_id=approval.approval_id,
    )

    assert result["approval_id"] == approval.approval_id
    assert result["status"] == "cancelled"

    # DB state
    res = await db.execute(select(Approval).where(Approval.approval_id == approval.approval_id))
    updated = res.scalar_one()
    assert updated.status == "cancelled"


# ---------------------------------------------------------------------------
# TEST-APP-007 — cancel another employee's submission raises 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_another_employee_submission_raises_403(db: AsyncSession):
    manager, employee_a = await _setup_team(db, "app007mgr@test.com", "app007a@test.com")
    employee_b = await _make_employee(
        db,
        email="app007b@test.com",
        manager_id=manager.employee_id,
    )

    approval = await _make_approval(
        db,
        employee_id=employee_a.employee_id,
        manager_id=manager.employee_id,
        week_start=WEEK_START,
        status="pending",
    )
    await db.commit()

    service = ApprovalService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel(
            employee_id=employee_b.employee_id,
            approval_id=approval.approval_id,
        )

    assert exc_info.value.status_code in (403, 404)


# ---------------------------------------------------------------------------
# TEST-APP-008 — cancel already approved submission raises 409/400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_already_approved_submission_raises_409(db: AsyncSession):
    manager, employee = await _setup_team(db, "app008mgr@test.com", "app008emp@test.com")
    approval = await _make_approval(
        db,
        employee_id=employee.employee_id,
        manager_id=manager.employee_id,
        week_start=WEEK_START,
        status="approved",
    )
    await db.commit()

    service = ApprovalService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel(
            employee_id=employee.employee_id,
            approval_id=approval.approval_id,
        )

    assert exc_info.value.status_code in (400, 409)


# ---------------------------------------------------------------------------
# TEST-APP-009 — get_pending returns only manager's team approvals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_pending_returns_only_manager_team_approvals(db: AsyncSession):
    # Manager A with 3 employees
    manager_a = await _make_employee(
        db, email="app009mgra@test.com", role="manager", first_name="Manager", last_name="A"
    )
    for i in range(3):
        emp = await _make_employee(
            db,
            email=f"app009empa{i}@test.com",
            manager_id=manager_a.employee_id,
        )
        await _make_approval(
            db,
            employee_id=emp.employee_id,
            manager_id=manager_a.employee_id,
            week_start=WEEK_START + timedelta(weeks=i),
            status="pending",
        )

    # Manager B with 2 employees (different org)
    org2 = await _make_org(db, org_id=10)
    manager_b = await _make_employee(
        db, email="app009mgrb@test.com", role="manager", org_id=10, first_name="Manager", last_name="B"
    )
    for i in range(2):
        emp_b = await _make_employee(
            db,
            email=f"app009empb{i}@test.com",
            manager_id=manager_b.employee_id,
            org_id=10,
        )
        await _make_approval(
            db,
            employee_id=emp_b.employee_id,
            manager_id=manager_b.employee_id,
            week_start=WEEK_START + timedelta(weeks=i),
            status="pending",
        )

    await db.commit()

    service = ApprovalService(db)
    approvals_a = await service.get_pending_for_manager(manager_a.employee_id)
    approvals_b = await service.get_pending_for_manager(manager_b.employee_id)

    assert len(approvals_a) == 3
    assert len(approvals_b) == 2

    # None of manager_b's employees should appear in manager_a's list
    a_employee_ids = {a["employee_id"] for a in approvals_a}
    b_employee_ids = {a["employee_id"] for a in approvals_b}
    assert a_employee_ids.isdisjoint(b_employee_ids)
