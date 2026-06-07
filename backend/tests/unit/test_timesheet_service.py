"""Unit tests for TimesheetService — TEST-TS-001 through TEST-TS-020."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.approval import Approval
from app.models.timesheet_entry import TimesheetEntry
from app.services.timesheet_service import TimesheetService

from tests.unit.conftest import (
    _make_client,
    _make_employee,
    _make_entry,
    _make_org,
    _make_org_settings,
    _make_project,
    _make_approval,
)

# A safe past date (always in the past regardless of when tests run)
PAST_DATE = date(2026, 5, 5)
FUTURE_DATE = date.today() + timedelta(days=1)
WEEK_STR = "2026-W19"  # week containing 2026-05-04 (Mon) → 2026-05-10 (Sun)


# ---------------------------------------------------------------------------
# TEST-TS-001 — valid entry returns draft
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_entry_valid_data_returns_draft(db: AsyncSession):
    await _make_org_settings(db, max_hours_per_day=10.0)
    emp = await _make_employee(db, email="ts001@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    await db.commit()

    service = TimesheetService(db)
    result = await service.create_entry(
        employee_id=emp.employee_id,
        data={
            "project_id": project.project_id,
            "work_date": PAST_DATE,
            "hours_worked": 8,
            "description": "Development work",
            "entry_type": "normal",
            "task_type": "dev",
        },
    )

    assert result["status"] == "draft"
    assert result["hours_worked"] == 8.0
    assert result["employee_id"] == emp.employee_id

    # Verify it persists in DB without soft-delete
    res = await db.execute(
        select(TimesheetEntry).where(
            TimesheetEntry.timesheet_entry_id == result["timesheet_entry_id"]
        )
    )
    entry = res.scalar_one_or_none()
    assert entry is not None
    assert entry.deleted_at is None


# ---------------------------------------------------------------------------
# TEST-TS-002 — future work_date raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_entry_future_date_raises_422(db: AsyncSession):
    await _make_org_settings(db, max_hours_per_day=10.0)
    emp = await _make_employee(db, email="ts002@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_entry(
            employee_id=emp.employee_id,
            data={
                "project_id": project.project_id,
                "work_date": FUTURE_DATE,
                "hours_worked": 8,
                "description": "Future work",
                "entry_type": "normal",
                "task_type": "dev",
            },
        )

    assert exc_info.value.status_code == 422
    assert "futur" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# TEST-TS-003 — project not found raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_entry_project_not_assigned_raises_403(db: AsyncSession):
    await _make_org_settings(db, max_hours_per_day=10.0)
    emp = await _make_employee(db, email="ts003@test.com")
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_entry(
            employee_id=emp.employee_id,
            data={
                "project_id": 99999,
                "work_date": PAST_DATE,
                "hours_worked": 8,
                "description": "Unknown project",
                "entry_type": "normal",
                "task_type": "dev",
            },
        )

    assert exc_info.value.status_code in (403, 404, 422)


# ---------------------------------------------------------------------------
# TEST-TS-004 — exceeds max daily hours raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_entry_exceeds_max_daily_hours_raises_422(db: AsyncSession):
    await _make_org_settings(db, max_hours_per_day=10.0)
    emp = await _make_employee(db, email="ts004@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    # Another project for the second entry
    project2 = await _make_project(db, client.client_id, emp.employee_id, name="Project Beta")
    await db.commit()

    # Pre-populate 8h for the day
    await _make_entry(db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0)
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_entry(
            employee_id=emp.employee_id,
            data={
                "project_id": project2.project_id,
                "work_date": PAST_DATE,
                "hours_worked": 4,  # 8 + 4 = 12 > max_hours_per_day=10
                "description": "Overflow work",
                "entry_type": "normal",
                "task_type": "dev",
            },
        )

    assert exc_info.value.status_code == 422
    assert "dépasserait" in exc_info.value.detail.lower() or "max" in exc_info.value.detail.lower() or "exceed" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# TEST-TS-005 — duplicate entry raises 409
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_entry_duplicate_raises_409(db: AsyncSession):
    await _make_org_settings(db, max_hours_per_day=24.0)
    emp = await _make_employee(db, email="ts005@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    await db.commit()

    # Create first entry
    await _make_entry(db, emp.employee_id, project.project_id, PAST_DATE, hours=4.0)
    await db.commit()

    service = TimesheetService(db)
    # Attempt to create the same entry (same employee/project/date/type)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_entry(
            employee_id=emp.employee_id,
            data={
                "project_id": project.project_id,
                "work_date": PAST_DATE,
                "hours_worked": 4,
                "description": "Duplicate",
                "entry_type": "normal",  # same type
                "task_type": "dev",
            },
        )

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# TEST-TS-006 — hours below minimum raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_entry_below_minimum_hours_raises_422(db: AsyncSession):
    await _make_org_settings(db, max_hours_per_day=10.0)
    emp = await _make_employee(db, email="ts006@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_entry(
            employee_id=emp.employee_id,
            data={
                "project_id": project.project_id,
                "work_date": PAST_DATE,
                "hours_worked": 0.1,  # below 0.25
                "description": "Too short",
                "entry_type": "normal",
                "task_type": "dev",
            },
        )

    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# TEST-TS-007 — update draft entry updates hours
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_draft_entry_updates_hours(db: AsyncSession):
    emp = await _make_employee(db, email="ts007@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    entry = await _make_entry(db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0)
    await db.commit()

    service = TimesheetService(db)
    result = await service.update_entry(
        employee_id=emp.employee_id,
        entry_id=entry.timesheet_entry_id,
        data={"hours_worked": 7.5},
    )

    assert result["hours_worked"] == 7.5
    assert result["status"] == "draft"


# ---------------------------------------------------------------------------
# TEST-TS-008 — update rejected entry reverts to draft
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_rejected_entry_reverts_to_draft(db: AsyncSession):
    emp = await _make_employee(db, email="ts008@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    entry = await _make_entry(
        db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0, status="rejected"
    )
    await db.commit()

    service = TimesheetService(db)
    result = await service.update_entry(
        employee_id=emp.employee_id,
        entry_id=entry.timesheet_entry_id,
        data={"hours_worked": 7.0},
    )

    assert result["status"] == "draft"
    assert result["hours_worked"] == 7.0


# ---------------------------------------------------------------------------
# TEST-TS-009 — update submitted entry raises 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_submitted_entry_raises_403(db: AsyncSession):
    emp = await _make_employee(db, email="ts009@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    entry = await _make_entry(
        db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0, status="submitted"
    )
    original_hours = float(entry.hours_worked)
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.update_entry(
            employee_id=emp.employee_id,
            entry_id=entry.timesheet_entry_id,
            data={"hours_worked": 5.0},
        )

    assert exc_info.value.status_code in (403, 409)

    # Entry must remain unchanged in DB
    res = await db.execute(
        select(TimesheetEntry).where(
            TimesheetEntry.timesheet_entry_id == entry.timesheet_entry_id
        )
    )
    unchanged = res.scalar_one()
    assert float(unchanged.hours_worked) == original_hours


# ---------------------------------------------------------------------------
# TEST-TS-010 — update approved entry raises 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_approved_entry_raises_403(db: AsyncSession):
    emp = await _make_employee(db, email="ts010@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    entry = await _make_entry(
        db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0, status="approved"
    )
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.update_entry(
            employee_id=emp.employee_id,
            entry_id=entry.timesheet_entry_id,
            data={"hours_worked": 5.0},
        )

    assert exc_info.value.status_code in (403, 409)


# ---------------------------------------------------------------------------
# TEST-TS-011 — update another employee's entry raises 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_entry_of_another_employee_raises_403(db: AsyncSession):
    emp_a = await _make_employee(db, email="ts011a@test.com")
    emp_b = await _make_employee(db, email="ts011b@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp_a.employee_id, team_members=[emp_a.employee_id, emp_b.employee_id])
    entry = await _make_entry(db, emp_a.employee_id, project.project_id, PAST_DATE, hours=8.0)
    await db.commit()

    service = TimesheetService(db)
    # emp_b tries to edit emp_a's entry
    with pytest.raises(HTTPException) as exc_info:
        await service.update_entry(
            employee_id=emp_b.employee_id,
            entry_id=entry.timesheet_entry_id,
            data={"hours_worked": 5.0},
        )

    assert exc_info.value.status_code in (403, 404)


# ---------------------------------------------------------------------------
# TEST-TS-012 — delete draft entry soft-deletes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_draft_entry_soft_deletes(db: AsyncSession):
    emp = await _make_employee(db, email="ts012@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    entry = await _make_entry(db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0)
    await db.commit()

    service = TimesheetService(db)
    result = await service.delete_entry(emp.employee_id, entry.timesheet_entry_id)

    assert result is None

    # deleted_at must be set — query directly without soft-delete filter
    res = await db.execute(
        select(TimesheetEntry.deleted_at).where(
            TimesheetEntry.timesheet_entry_id == entry.timesheet_entry_id
        )
    )
    deleted_at_val = res.scalar_one_or_none()
    assert deleted_at_val is not None


# ---------------------------------------------------------------------------
# TEST-TS-013 — delete non-draft entry raises 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_non_draft_entry_raises_403(db: AsyncSession):
    emp = await _make_employee(db, email="ts013@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    entry = await _make_entry(
        db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0, status="submitted"
    )
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.delete_entry(emp.employee_id, entry.timesheet_entry_id)

    assert exc_info.value.status_code in (403, 422)

    # deleted_at must remain None
    res = await db.execute(
        select(TimesheetEntry.deleted_at).where(
            TimesheetEntry.timesheet_entry_id == entry.timesheet_entry_id
        )
    )
    assert res.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# TEST-TS-014 — submit_week first time creates approval
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_week_first_time_creates_approval(db: AsyncSession):
    manager = await _make_employee(
        db, email="ts014mgr@test.com", role="manager"
    )
    emp = await _make_employee(db, email="ts014emp@test.com", manager_id=manager.employee_id)
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, manager.employee_id)
    await db.commit()

    # Create 5 draft entries for week 2026-W19 (Mon 2026-05-04 → Fri 2026-05-08)
    week_dates = [date(2026, 5, 4), date(2026, 5, 5), date(2026, 5, 6), date(2026, 5, 7), date(2026, 5, 8)]
    for d in week_dates:
        await _make_entry(db, emp.employee_id, project.project_id, d, hours=8.0)
    await db.commit()

    with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
        service = TimesheetService(db)
        result = await service.submit_week(emp.employee_id, WEEK_STR)

    assert result["entries_submitted"] == 5
    assert "approval_id" in result

    # All entries should be submitted
    res = await db.execute(
        select(TimesheetEntry).where(
            TimesheetEntry.employee_id == emp.employee_id,
            TimesheetEntry.status == "submitted",
        )
    )
    submitted_entries = res.scalars().all()
    assert len(submitted_entries) == 5

    # Approval should exist with pending status
    approval_res = await db.execute(
        select(Approval).where(Approval.approval_id == result["approval_id"])
    )
    approval = approval_res.scalar_one_or_none()
    assert approval is not None
    assert approval.status == "pending"


# ---------------------------------------------------------------------------
# TEST-TS-015 — submit_week resubmission after rejection reuses approval
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_week_resubmission_after_rejection(db: AsyncSession):
    manager = await _make_employee(db, email="ts015mgr@test.com", role="manager")
    emp = await _make_employee(db, email="ts015emp@test.com", manager_id=manager.employee_id)
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, manager.employee_id)

    # Existing rejected approval for the same week
    existing_approval = await _make_approval(
        db,
        employee_id=emp.employee_id,
        manager_id=manager.employee_id,
        week_start=date(2026, 5, 4),
        status="rejected",
    )
    # Draft entries after correction
    await _make_entry(db, emp.employee_id, project.project_id, date(2026, 5, 4), hours=8.0)
    await _make_entry(db, emp.employee_id, project.project_id, date(2026, 5, 5), hours=8.0)
    await db.commit()

    with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
        service = TimesheetService(db)
        result = await service.submit_week(emp.employee_id, WEEK_STR)

    # Must reuse existing approval, not create a new one
    assert result["approval_id"] == existing_approval.approval_id

    # Approval status should be pending again
    res = await db.execute(
        select(Approval).where(Approval.approval_id == existing_approval.approval_id)
    )
    approval = res.scalar_one()
    assert approval.status == "pending"


# ---------------------------------------------------------------------------
# TEST-TS-016 — submit_week with no draft entries raises 400/422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_week_no_draft_entries_raises_422(db: AsyncSession):
    emp = await _make_employee(db, email="ts016@test.com")
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.submit_week(emp.employee_id, WEEK_STR)

    assert exc_info.value.status_code in (400, 422)


# ---------------------------------------------------------------------------
# TEST-TS-017 — submit_week no manager found raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_week_no_manager_found_raises_422(db: AsyncSession):
    """Employee belongs to a soft-deleted org — service raises 422 with no_valid_organization."""
    from app.models.organization import Organization
    from datetime import datetime, timezone

    # Create a soft-deleted organization (not found by get_by_id)
    deleted_org = Organization(
        org_id=50,
        org_name="Deleted Org",
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(deleted_org)
    await db.flush()

    # Create employee pointing to the deleted org (raw, bypassing the helper)
    from app.models.employee import Employee
    import bcrypt as _bcrypt
    emp = Employee(
        email="ts017@test.com",
        first_name="Test",
        last_name="User",
        password_hash=_bcrypt.hashpw(b"pass", _bcrypt.gensalt(rounds=4)).decode(),
        role="employee",
        employment_status="active",
        org_id=50,  # points to soft-deleted org
    )
    db.add(emp)
    await db.flush()
    await db.refresh(emp)

    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)
    await _make_entry(db, emp.employee_id, project.project_id, PAST_DATE, hours=8.0)
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.submit_week(emp.employee_id, "2026-W19")

    assert exc_info.value.status_code in (400, 404, 422)


# ---------------------------------------------------------------------------
# TEST-TS-018 — submit_week invalid format raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_week_invalid_format_raises_422(db: AsyncSession):
    emp = await _make_employee(db, email="ts018@test.com")
    await db.commit()

    service = TimesheetService(db)
    with pytest.raises((HTTPException, ValueError)) as exc_info:
        await service.submit_week(emp.employee_id, "2026-18")  # Invalid — missing 'W'

    if isinstance(exc_info.value, HTTPException):
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# TEST-TS-019 — get_week returns entries grouped by date
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_week_returns_entries_grouped_by_date(db: AsyncSession):
    emp = await _make_employee(db, email="ts019@test.com")
    client = await _make_client(db)
    project = await _make_project(db, client.client_id, emp.employee_id)

    # 3 entries across 2 days
    day1 = date(2026, 5, 4)  # Monday of W19
    day2 = date(2026, 5, 5)  # Tuesday

    await _make_entry(db, emp.employee_id, project.project_id, day1, hours=4.0)
    # Need a different entry_type to avoid unique constraint on same day/project
    entry2 = TimesheetEntry(
        employee_id=emp.employee_id,
        project_id=project.project_id,
        work_date=day1,
        hours_worked=Decimal("2.0"),
        description="Overtime",
        task_type="dev",
        entry_type="overtime",
        billable_flag=True,
        status="draft",
    )
    db.add(entry2)
    await _make_entry(db, emp.employee_id, project.project_id, day2, hours=8.0)
    await db.commit()

    service = TimesheetService(db)
    result = await service.get_week(emp.employee_id, WEEK_STR)

    assert "entries" in result
    entries_by_date = result["entries"]
    assert str(day1) in entries_by_date
    assert str(day2) in entries_by_date
    assert len(entries_by_date[str(day1)]) == 2
    assert len(entries_by_date[str(day2)]) == 1
    assert result["week_total"] == 14.0


# ---------------------------------------------------------------------------
# TEST-TS-020 — get_week empty week returns empty structure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_week_empty_week_returns_empty_dict(db: AsyncSession):
    emp = await _make_employee(db, email="ts020@test.com")
    await db.commit()

    service = TimesheetService(db)
    result = await service.get_week(emp.employee_id, WEEK_STR)

    assert "entries" in result
    assert result["entries"] == {} or result["entries"] == []
    assert result["week_total"] == 0.0 or result["week_total"] == 0
