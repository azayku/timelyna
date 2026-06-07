"""Tests for deferred employee onboarding (US-02).

12d.30 — create_employee_or_pending: future hire_date → PendingEmployee; past → Employee
12d.31 — activate_pending_employees: due today → created; future → ignored
12d.32 — POST /admin/users with hire_date 10 days out + lead_days=2 → pending with correct account_creation_date
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.org_settings import OrgSettings
from app.models.pending_employee import PendingEmployee
from tests.conftest import make_employee


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _admin_header(admin) -> dict:
    token = create_access_token({
        "sub": admin.email,
        "employee_id": admin.employee_id,
        "org_id": admin.org_id,
        "role": admin.role,
    })
    return {"Authorization": f"Bearer {token}"}


async def _ensure_org_settings(db: AsyncSession, lead_days: int = 2) -> OrgSettings:
    from sqlalchemy import select as _sel
    result = await db.execute(_sel(OrgSettings).where(OrgSettings.org_id == 1))
    org = result.scalar_one_or_none()
    if not org:
        org = OrgSettings(
            org_id=1,
            standard_hours_per_day=Decimal("8"),
            max_hours_per_day=Decimal("16"),
            account_creation_lead_days=lead_days,
        )
        db.add(org)
    else:
        org.account_creation_lead_days = lead_days
    await db.flush()
    return org


# ---------------------------------------------------------------------------
# 12d.30 — Unit: create_employee_or_pending routing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_future_hire_date_creates_pending(db: AsyncSession):
    """hire_date 10 days from now with lead_days=2 → PendingEmployee (account_creation_date = hire_date - 2)."""
    uid = _uid()
    await _ensure_org_settings(db, lead_days=2)

    from app.services.auth_service import AuthService
    svc = AuthService(db)

    hire_date = date.today() + timedelta(days=10)
    result = await svc.create_employee_or_pending(
        email=f"pending-{uid}@example.com",
        first_name="Alice",
        last_name="Future",
        role="employee",
        birth_date=date(1990, 1, 1),
        address="123 Rue Test",
        hire_date=hire_date,
    )

    assert result["type"] == "pending"
    assert result["account_creation_date"] == str(hire_date - timedelta(days=2))
    assert result["hire_date"] == str(hire_date)


@pytest.mark.asyncio
async def test_past_hire_date_creates_employee_immediately(db: AsyncSession):
    """hire_date in the past → Employee created immediately."""
    uid = _uid()
    await _ensure_org_settings(db, lead_days=2)

    from app.services.auth_service import AuthService
    svc = AuthService(db)

    hire_date = date.today() - timedelta(days=5)
    result = await svc.create_employee_or_pending(
        email=f"immediate-{uid}@example.com",
        first_name="Bob",
        last_name="Past",
        role="employee",
        birth_date=date(1985, 6, 15),
        address="456 Rue Test",
        hire_date=hire_date,
    )

    assert result["type"] == "employee"
    assert result["id"] > 0


@pytest.mark.asyncio
async def test_no_hire_date_creates_employee_immediately(db: AsyncSession):
    """No hire_date → Employee created immediately."""
    uid = _uid()
    await _ensure_org_settings(db, lead_days=2)

    from app.services.auth_service import AuthService
    svc = AuthService(db)

    result = await svc.create_employee_or_pending(
        email=f"nohire-{uid}@example.com",
        first_name="Carol",
        last_name="NoHire",
        role="employee",
        birth_date=date(1992, 3, 20),
        address="789 Rue Test",
        hire_date=None,
    )

    assert result["type"] == "employee"


@pytest.mark.asyncio
async def test_hire_date_exactly_lead_days_away_creates_employee(db: AsyncSession):
    """hire_date exactly lead_days away: account_creation_date = today → not deferred."""
    uid = _uid()
    await _ensure_org_settings(db, lead_days=2)

    from app.services.auth_service import AuthService
    svc = AuthService(db)

    # account_creation_date = today + 2 - 2 = today → not > today → immediate
    hire_date = date.today() + timedelta(days=2)
    result = await svc.create_employee_or_pending(
        email=f"boundary-{uid}@example.com",
        first_name="Dave",
        last_name="Boundary",
        role="employee",
        birth_date=date(1988, 9, 10),
        address="1 Rue Boundary",
        hire_date=hire_date,
    )

    assert result["type"] == "employee"


# ---------------------------------------------------------------------------
# 12d.31 — Unit: activate_pending_employees task logic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_activate_pending_due_today(db: AsyncSession):
    """Pending employee with account_creation_date = today → account created and record deleted."""
    uid = _uid()
    await _ensure_org_settings(db, lead_days=2)

    # Insert a pending employee due today
    pending = PendingEmployee(
        first_name="Eve",
        last_name="DueToday",
        email=f"due-today-{uid}@example.com",
        role="employee",
        hire_date=date.today() + timedelta(days=2),
        account_creation_date=date.today(),
        birth_date=date(1991, 4, 5),
        address="10 Rue Due",
    )
    db.add(pending)
    await db.flush()
    pending_id = pending.id

    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    from app.services.auth_service import AuthService
    from sqlalchemy import select as _sel

    repo = PendingEmployeeRepository(db)
    svc = AuthService(db)

    due = await repo.get_pending_due(date.today())
    assert any(p.id == pending_id for p in due)

    # Activate
    for p in due:
        if p.id == pending_id:
            employee = await svc.create_employee(
                email=p.email,
                first_name=p.first_name,
                last_name=p.last_name,
                role=p.role,
                birth_date=p.birth_date,
                address=p.address,
            )
            await repo.delete(p.id)
            await db.commit()

            # Verify employee was created
            assert employee.employee_id > 0
            assert employee.email == p.email

            # Verify pending record is gone
            gone = await repo.get_by_id(pending_id)
            assert gone is None
            break


@pytest.mark.asyncio
async def test_future_pending_not_activated(db: AsyncSession):
    """Pending employee with account_creation_date in the future → not returned by get_pending_due."""
    uid = _uid()

    pending = PendingEmployee(
        first_name="Frank",
        last_name="Future",
        email=f"future-{uid}@example.com",
        role="employee",
        hire_date=date.today() + timedelta(days=10),
        account_creation_date=date.today() + timedelta(days=8),
        birth_date=date(1993, 7, 22),
        address="20 Rue Future",
    )
    db.add(pending)
    await db.flush()

    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    repo = PendingEmployeeRepository(db)

    due = await repo.get_pending_due(date.today())
    assert not any(p.id == pending.id for p in due)


# ---------------------------------------------------------------------------
# 12d.32 — Integration: POST /admin/users with future hire_date → pending
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_post_admin_users_future_hire_date_creates_pending(
    client: AsyncClient, db: AsyncSession
):
    """POST /admin/users with hire_date 10 days out and lead_days=2 → pending_employee with correct account_creation_date."""
    uid = _uid()
    admin = await make_employee(db, email=f"admin-{uid}@example.com", role="admin")
    await _ensure_org_settings(db, lead_days=2)

    hire_date = date.today() + timedelta(days=10)
    expected_creation_date = hire_date - timedelta(days=2)

    resp = await client.post(
        "/api/v1/admin/users",
        headers=_admin_header(admin),
        json={
            "email": f"newpending-{uid}@example.com",
            "first_name": "Grace",
            "last_name": "Pending",
            "role": "employee",
            "birth_date": "1995-03-15",
            "address": "30 Rue Pending",
            "hire_date": str(hire_date),
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["type"] == "pending"
    assert data["account_creation_date"] == str(expected_creation_date)
    assert data["hire_date"] == str(hire_date)


@pytest.mark.asyncio
async def test_post_admin_users_past_hire_date_creates_employee(
    client: AsyncClient, db: AsyncSession
):
    """POST /admin/users with past hire_date → employee created immediately."""
    uid = _uid()
    admin = await make_employee(db, email=f"admin2-{uid}@example.com", role="admin")
    await _ensure_org_settings(db, lead_days=2)

    hire_date = date.today() - timedelta(days=3)

    resp = await client.post(
        "/api/v1/admin/users",
        headers=_admin_header(admin),
        json={
            "email": f"immediate2-{uid}@example.com",
            "first_name": "Henry",
            "last_name": "Immediate",
            "role": "employee",
            "birth_date": "1988-11-20",
            "address": "40 Rue Immediate",
            "hire_date": str(hire_date),
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["type"] == "employee"
    assert data["id"] > 0
