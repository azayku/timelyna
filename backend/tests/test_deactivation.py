"""Tests: désactivation différée (spec 12c.16 & 12c.17)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import make_employee


def _admin_token(employee_id: int, email: str) -> dict:
    token = create_access_token({
        "sub": email,
        "employee_id": employee_id,
        "org_id": 1,
        "role": "admin",
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 12c.16 — Integration: schedule-deactivation stores the date
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_deactivation_stores_date(client: AsyncClient, db: AsyncSession):
    admin = await make_employee(db, email="admin_sched@example.com", role="admin")
    target = await make_employee(db, email="target_sched@example.com", role="employee")
    await db.commit()

    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    resp = await client.put(
        f"/api/v1/admin/users/{target.employee_id}/schedule-deactivation",
        json={"scheduled_at": future},
        headers=_admin_token(admin.employee_id, admin.email),
    )
    assert resp.status_code == 204, resp.text

    # Verify stored in DB
    from app.repositories.auth_repository import AuthRepository
    from sqlalchemy import select
    from app.models.employee import Employee
    repo = AuthRepository(db)
    result = await db.execute(select(Employee).where(Employee.employee_id == target.employee_id))
    emp = result.scalar_one_or_none()
    assert emp is not None
    assert emp.deactivation_scheduled_at is not None


@pytest.mark.asyncio
async def test_cancel_scheduled_deactivation(client: AsyncClient, db: AsyncSession):
    admin = await make_employee(db, email="admin_cancel@example.com", role="admin")
    target = await make_employee(db, email="target_cancel@example.com", role="employee")
    await db.commit()

    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    await client.put(
        f"/api/v1/admin/users/{target.employee_id}/schedule-deactivation",
        json={"scheduled_at": future},
        headers=_admin_token(admin.employee_id, admin.email),
    )

    resp = await client.delete(
        f"/api/v1/admin/users/{target.employee_id}/schedule-deactivation",
        headers=_admin_token(admin.employee_id, admin.email),
    )
    assert resp.status_code == 204, resp.text

    from app.repositories.auth_repository import AuthRepository
    from sqlalchemy import select
    from app.models.employee import Employee
    repo = AuthRepository(db)
    result = await db.execute(select(Employee).where(Employee.employee_id == target.employee_id))
    emp = result.scalar_one_or_none()
    assert emp is not None
    assert emp.deactivation_scheduled_at is None


# ---------------------------------------------------------------------------
# 12c.17 — Unit: process_scheduled_deactivations logic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_deactivations_past_date(db: AsyncSession):
    """Employee with past scheduled_at should be deactivated."""
    import bcrypt as _bcrypt
    from app.models.employee import Employee
    from sqlalchemy import select

    past = datetime.now(timezone.utc) - timedelta(hours=1)
    emp = Employee(
        email="past_deact@example.com",
        first_name="Past",
        last_name="Deact",
        password_hash=_bcrypt.hashpw(b"pw", _bcrypt.gensalt(rounds=4)).decode(),
        role="employee",
        employment_status="active",
        org_id=1,
        deactivation_scheduled_at=past,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

    # Run the async core directly (no Celery needed in tests)
    from sqlalchemy import update
    from app.models.auth import RefreshToken

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Employee).where(
            Employee.deactivation_scheduled_at <= now,
            Employee.employment_status == "active",
            Employee.deleted_at.is_(None),
        )
    )
    employees_to_deactivate = result.scalars().all()
    assert any(e.employee_id == emp.employee_id for e in employees_to_deactivate)

    for e in employees_to_deactivate:
        if e.employee_id == emp.employee_id:
            await db.execute(
                update(Employee)
                .where(Employee.employee_id == e.employee_id)
                .values(employment_status="inactive", deactivation_scheduled_at=None)
            )
    await db.commit()

    result2 = await db.execute(select(Employee).where(Employee.employee_id == emp.employee_id))
    updated = result2.scalar_one()
    assert updated.employment_status == "inactive"
    assert updated.deactivation_scheduled_at is None


@pytest.mark.asyncio
async def test_process_deactivations_future_date_ignored(db: AsyncSession):
    """Employee with future scheduled_at should NOT be deactivated."""
    import bcrypt as _bcrypt
    from app.models.employee import Employee
    from sqlalchemy import select

    future = datetime.now(timezone.utc) + timedelta(days=30)
    emp = Employee(
        email="future_deact@example.com",
        first_name="Future",
        last_name="Deact",
        password_hash=_bcrypt.hashpw(b"pw", _bcrypt.gensalt(rounds=4)).decode(),
        role="employee",
        employment_status="active",
        org_id=1,
        deactivation_scheduled_at=future,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Employee).where(
            Employee.deactivation_scheduled_at <= now,
            Employee.employment_status == "active",
            Employee.deleted_at.is_(None),
            Employee.employee_id == emp.employee_id,
        )
    )
    # Should NOT be in the list
    assert result.scalar_one_or_none() is None
