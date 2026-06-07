"""Tests for the approvals workflow — tasks 3.11, 3.12, 3.13, 3.14."""
from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.timesheet_repository import TimesheetRepository
from app.services.approval_service import ApprovalService
from tests.conftest import make_client, make_employee, make_entry, make_project


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _auth(employee) -> dict:
    token = create_access_token({
        "sub": employee.email,
        "employee_id": employee.employee_id,
        "org_id": employee.org_id,
        "role": employee.role,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def setup(db: AsyncSession):
    """
    Creates:
      - manager (role=manager)
      - employee (reports to manager)
      - other_manager (role=manager, unrelated)
      - client + project
    """
    uid = _uid()
    manager = await make_employee(db, email=f"mgr-{uid}@example.com", role="manager")
    emp = await make_employee(
        db, email=f"emp-{uid}@example.com", role="employee", manager_id=manager.employee_id
    )
    other_mgr = await make_employee(db, email=f"othermgr-{uid}@example.com", role="manager")
    admin = await make_employee(db, email=f"admin-{uid}@example.com", role="admin")
    cli = await make_client(db, name=f"Client-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    await db.commit()
    return {
        "manager": manager,
        "emp": emp,
        "other_mgr": other_mgr,
        "admin": admin,
        "proj": proj,
        "uid": uid,
    }


async def _submit_week(db: AsyncSession, emp, proj, week_start: date) -> int:
    """Helper: create an entry and submit the week, return approval_id."""
    entry = await make_entry(db, emp.employee_id, proj.project_id, week_start)
    await db.commit()

    ts_repo = TimesheetRepository(db)
    approval = await ts_repo.create_approval(emp.employee_id, emp.manager_id, week_start)
    await ts_repo.submit_week_entries(emp.employee_id, week_start, week_start)
    await db.commit()
    return approval.approval_id


# ---------------------------------------------------------------------------
# 3.11 — Unit tests: approve
# ---------------------------------------------------------------------------

async def test_approve_success(db: AsyncSession, setup):
    """Manager approves their direct report's submission → status=approved, entries=approved."""
    emp = setup["emp"]
    manager = setup["manager"]
    proj = setup["proj"]

    week_start = date(2024, 1, 8)  # unique week
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    result = await svc.approve(manager.employee_id, approval_id, notes="Looks good")

    assert result["status"] == "approved"

    # Verify approval record
    repo = ApprovalRepository(db)
    approval = await repo.get_by_id(approval_id)
    assert approval.status == "approved"
    assert approval.manager_id == manager.employee_id
    assert approval.notes == "Looks good"
    assert approval.decided_at is not None

    # Verify entries are approved
    ts_repo = TimesheetRepository(db)
    entries = await ts_repo.get_week(emp.employee_id, week_start, week_start)
    assert all(e.status == "approved" for e in entries)
    assert all(e.approved_at is not None for e in entries)


async def test_approve_wrong_manager(db: AsyncSession, setup):
    """A manager who is NOT the employee's manager gets 403."""
    emp = setup["emp"]
    other_mgr = setup["other_mgr"]
    proj = setup["proj"]

    week_start = date(2024, 1, 15)
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.approve(other_mgr.employee_id, approval_id)
    assert exc_info.value.status_code == 403


async def test_approve_already_approved(db: AsyncSession, setup):
    """Approving an already-approved submission returns 409."""
    emp = setup["emp"]
    manager = setup["manager"]
    proj = setup["proj"]

    week_start = date(2024, 1, 22)
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    await svc.approve(manager.employee_id, approval_id)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.approve(manager.employee_id, approval_id)
    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 3.12 — Unit tests: reject
# ---------------------------------------------------------------------------

async def test_reject_success(db: AsyncSession, setup):
    """Manager rejects with valid reason → status=rejected, entries back to draft."""
    emp = setup["emp"]
    manager = setup["manager"]
    proj = setup["proj"]

    week_start = date(2024, 2, 5)
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    result = await svc.reject(
        manager.employee_id, approval_id, rejection_reason="Hours look incorrect, please fix"
    )
    assert result["status"] == "rejected"

    repo = ApprovalRepository(db)
    approval = await repo.get_by_id(approval_id)
    assert approval.status == "rejected"
    assert approval.rejection_reason == "Hours look incorrect, please fix"

    # Entries should be back to draft
    ts_repo = TimesheetRepository(db)
    entries = await ts_repo.get_week(emp.employee_id, week_start, week_start)
    assert all(e.status == "draft" for e in entries)


async def test_reject_missing_reason(db: AsyncSession, setup):
    """Rejection reason shorter than 10 chars → 422."""
    emp = setup["emp"]
    manager = setup["manager"]
    proj = setup["proj"]

    week_start = date(2024, 2, 12)
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.reject(manager.employee_id, approval_id, rejection_reason="Too short")
    assert exc_info.value.status_code == 422


async def test_reject_wrong_status(db: AsyncSession, setup):
    """Rejecting an already-approved submission → 409."""
    emp = setup["emp"]
    manager = setup["manager"]
    proj = setup["proj"]

    week_start = date(2024, 2, 19)
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    await svc.approve(manager.employee_id, approval_id)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.reject(
            manager.employee_id, approval_id, rejection_reason="Should not work at all"
        )
    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 3.13 — Unit tests: cancel
# ---------------------------------------------------------------------------

async def test_cancel_success(db: AsyncSession, setup):
    """Employee cancels their own pending submission → status=cancelled, entries=draft."""
    emp = setup["emp"]
    proj = setup["proj"]

    week_start = date(2024, 3, 4)
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    result = await svc.cancel(emp.employee_id, approval_id)
    assert result["status"] == "cancelled"

    repo = ApprovalRepository(db)
    approval = await repo.get_by_id(approval_id)
    assert approval.status == "cancelled"

    ts_repo = TimesheetRepository(db)
    entries = await ts_repo.get_week(emp.employee_id, week_start, week_start)
    assert all(e.status == "draft" for e in entries)


async def test_cancel_not_pending(db: AsyncSession, setup):
    """Cancelling an already-approved submission → 400."""
    emp = setup["emp"]
    manager = setup["manager"]
    proj = setup["proj"]

    week_start = date(2024, 3, 11)
    approval_id = await _submit_week(db, emp, proj, week_start)

    svc = ApprovalService(db)
    await svc.approve(manager.employee_id, approval_id)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.cancel(emp.employee_id, approval_id)
    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# 3.14 — Integration test: submit → approve full flow
# ---------------------------------------------------------------------------

async def test_submit_approve_full_flow(client: AsyncClient, db: AsyncSession, setup):
    """
    Full flow via HTTP:
    1. Employee creates entries
    2. Employee submits week
    3. Manager approves
    4. All entries are 'approved'
    """
    emp = setup["emp"]
    manager = setup["manager"]
    proj = setup["proj"]

    # Step 1: create entries for a unique week
    week = "2024-W20"
    work_dates = [date(2024, 5, 13), date(2024, 5, 14)]
    for d in work_dates:
        entry = await make_entry(db, emp.employee_id, proj.project_id, d, hours=8.0)
    await db.commit()

    # Step 2: submit week
    submit_resp = await client.post(
        "/api/v1/employee/timesheet/submit",
        json={"week": week},
        headers=_auth(emp),
    )
    assert submit_resp.status_code == 200, submit_resp.text
    approval_id = submit_resp.json()["approval_id"]

    # Step 3: manager approves via HTTP
    approve_resp = await client.post(
        f"/api/v1/manager/approvals/{approval_id}/approve",
        json={"notes": "All good"},
        headers=_auth(manager),
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "approved"

    # Step 4: verify all entries are approved
    ts_repo = TimesheetRepository(db)
    for d in work_dates:
        entries = await ts_repo.get_week(emp.employee_id, d, d)
        assert all(e.status == "approved" for e in entries), f"Entry on {d} not approved"
        assert all(e.approved_at is not None for e in entries)
