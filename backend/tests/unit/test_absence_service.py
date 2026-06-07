"""Unit tests for AbsenceService — TEST-ABS-001 through TEST-ABS-008."""
from __future__ import annotations

from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.absence import Absence
from app.services.absence_service import AbsenceService

from tests.unit.conftest import _make_employee, _make_org


# ---------------------------------------------------------------------------
# TEST-ABS-001 — create valid absence request success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_absence_valid_request_success(db: AsyncSession):
    manager = await _make_employee(db, email="abs001mgr@test.com", role="manager")
    employee = await _make_employee(
        db,
        email="abs001emp@test.com",
        role="employee",
        manager_id=manager.employee_id,
    )
    await db.commit()

    service = AbsenceService(db)
    result = await service.create(
        employee_id=employee.employee_id,
        absence_type="cp",
        start_date=date(2026, 5, 12),
        end_date=date(2026, 5, 14),
        notes="Family vacation",
    )

    assert result["status"] == "pending"
    assert result["absence_type"] == "cp"
    assert result["start_date"] == "2026-05-12"
    assert result["end_date"] == "2026-05-14"
    assert result["employee_id"] == employee.employee_id


# ---------------------------------------------------------------------------
# TEST-ABS-002 — end_date before start_date raises 422/400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_absence_end_before_start_raises_422(db: AsyncSession):
    employee = await _make_employee(db, email="abs002@test.com")
    await db.commit()

    service = AbsenceService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.create(
            employee_id=employee.employee_id,
            absence_type="cp",
            start_date=date(2026, 5, 14),
            end_date=date(2026, 5, 12),  # end before start
        )

    assert exc_info.value.status_code in (400, 422)


# ---------------------------------------------------------------------------
# TEST-ABS-003 — sick leave does not require cp balance check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_absence_sick_leave_no_balance_required(db: AsyncSession):
    # Employee with 0 remaining leave days
    employee = await _make_employee(
        db,
        email="abs003@test.com",
        annual_leave_days=0,
    )
    await db.commit()

    service = AbsenceService(db)
    # sick leave should not be blocked even with 0 cp days
    result = await service.create(
        employee_id=employee.employee_id,
        absence_type="sick_leave",
        start_date=date(2026, 5, 12),
        end_date=date(2026, 5, 13),
    )

    assert result["status"] == "pending"
    assert result["absence_type"] == "sick_leave"


# ---------------------------------------------------------------------------
# TEST-ABS-004 — approve absence success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_absence_success(db: AsyncSession):
    manager = await _make_employee(db, email="abs004mgr@test.com", role="manager")
    employee = await _make_employee(
        db,
        email="abs004emp@test.com",
        manager_id=manager.employee_id,
    )
    await db.commit()

    # Create absence first
    service = AbsenceService(db)
    created = await service.create(
        employee_id=employee.employee_id,
        absence_type="cp",
        start_date=date(2026, 5, 12),
        end_date=date(2026, 5, 14),
    )

    result = await service.approve(
        manager_id=manager.employee_id,
        absence_id=created["id"],
    )

    assert result["status"] == "approved"
    assert result["approved_by"] == manager.employee_id
    assert result["approved_at"] is not None

    # Verify DB
    res = await db.execute(select(Absence).where(Absence.id == created["id"]))
    absence = res.scalar_one()
    assert absence.status == "approved"
    assert absence.approved_by == manager.employee_id


# ---------------------------------------------------------------------------
# TEST-ABS-005 — approve by wrong manager raises 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_absence_by_wrong_manager_raises_403(db: AsyncSession):
    # Manager C manages employee
    manager_c = await _make_employee(db, email="abs005mgrc@test.com", role="manager")
    employee = await _make_employee(
        db,
        email="abs005emp@test.com",
        manager_id=manager_c.employee_id,
    )

    # Manager D is unrelated (different org)
    org2 = await _make_org(db, org_id=20)
    manager_d = await _make_employee(
        db,
        email="abs005mgrd@test.com",
        role="manager",
        org_id=20,
    )
    await db.commit()

    service = AbsenceService(db)
    created = await service.create(
        employee_id=employee.employee_id,
        absence_type="cp",
        start_date=date(2026, 5, 12),
        end_date=date(2026, 5, 14),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.approve(
            manager_id=manager_d.employee_id,
            absence_id=created["id"],
        )

    assert exc_info.value.status_code in (403, 404)


# ---------------------------------------------------------------------------
# TEST-ABS-006 — reject absence with reason success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_absence_with_reason_success(db: AsyncSession):
    manager = await _make_employee(db, email="abs006mgr@test.com", role="manager")
    employee = await _make_employee(
        db,
        email="abs006emp@test.com",
        manager_id=manager.employee_id,
    )
    await db.commit()

    service = AbsenceService(db)
    created = await service.create(
        employee_id=employee.employee_id,
        absence_type="cp",
        start_date=date(2026, 5, 12),
        end_date=date(2026, 5, 14),
    )

    result = await service.reject(
        manager_id=manager.employee_id,
        absence_id=created["id"],
        reason="Période de forte activité",
    )

    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "Période de forte activité"

    # DB state
    res = await db.execute(select(Absence).where(Absence.id == created["id"]))
    absence = res.scalar_one()
    assert absence.status == "rejected"
    assert absence.rejection_reason == "Période de forte activité"


# ---------------------------------------------------------------------------
# TEST-ABS-007 — get_leave_balance calculates correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_leave_balance_calculates_correctly(db: AsyncSession):
    manager = await _make_employee(db, email="abs007mgr@test.com", role="manager")
    employee = await _make_employee(
        db,
        email="abs007emp@test.com",
        annual_leave_days=25,
        manager_id=manager.employee_id,
    )
    await db.commit()

    service = AbsenceService(db)

    # Create 2 approved cp absences of 3 days each
    abs1 = Absence(
        employee_id=employee.employee_id,
        absence_type="cp",
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 7),  # 3 days
        status="approved",
    )
    abs2 = Absence(
        employee_id=employee.employee_id,
        absence_type="cp",
        start_date=date(2026, 2, 10),
        end_date=date(2026, 2, 12),  # 3 days
        status="approved",
    )
    db.add(abs1)
    db.add(abs2)
    await db.commit()

    result = await service.get_leave_balance(employee.employee_id, 2026)

    assert result["annual_leave_days"] == 25
    assert result["days_taken"] == 6
    assert result["days_remaining"] == 19


# ---------------------------------------------------------------------------
# TEST-ABS-008 — pending absences not counted in leave balance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_leave_balance_pending_absences_not_counted(db: AsyncSession):
    employee = await _make_employee(
        db,
        email="abs008@test.com",
        annual_leave_days=25,
    )
    await db.commit()

    # Pending absence (should not count)
    pending_abs = Absence(
        employee_id=employee.employee_id,
        absence_type="cp",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 5),  # 5 days
        status="pending",
    )
    db.add(pending_abs)
    await db.commit()

    service = AbsenceService(db)
    result = await service.get_leave_balance(employee.employee_id, 2026)

    # Pending absences must not be counted
    assert result["days_taken"] == 0
    assert result["days_remaining"] == 25
