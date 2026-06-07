"""Tests — spec 12c : profil employé (birth_date, address) + désactivation différée.

Covers:
  12c.9  — création employé sans birth_date → 422
           création employé sans address → 422
           création employé avec birth_date dans le futur → 422
  12c.16 — PUT /admin/users/{id}/schedule-deactivation → 204, deactivation_scheduled_at stocké
  12c.17 — process_scheduled_deactivations :
             date passée → employé désactivé
             date future → ignoré
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.employee import Employee
from tests.conftest import make_employee


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _auth(employee: Employee) -> dict:
    token = create_access_token({
        "sub": employee.email,
        "employee_id": employee.employee_id,
        "org_id": employee.org_id,
        "role": employee.role,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def admin(db: AsyncSession) -> Employee:
    uid = _uid()
    emp = await make_employee(db, email=f"admin-{uid}@example.com", role="admin")
    await db.commit()
    return emp


# ===========================================================================
# 12c.9 — Validation création employé
# ===========================================================================

@pytest.mark.asyncio
async def test_create_employee_without_birth_date(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """POST /admin/users sans birth_date → 422."""
    uid = _uid()
    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": f"nobd-{uid}@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "role": "employee",
            "address": "12 Rue de la Paix, Paris",
            # birth_date intentionnellement absent
        },
        headers=_auth(admin),
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_create_employee_without_address(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """POST /admin/users sans address → 422."""
    uid = _uid()
    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": f"noaddr-{uid}@example.com",
            "first_name": "Marie",
            "last_name": "Martin",
            "role": "employee",
            "birth_date": "1990-05-15",
            # address intentionnellement absent
        },
        headers=_auth(admin),
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_create_employee_with_future_birth_date(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """POST /admin/users avec birth_date dans le futur → 422."""
    uid = _uid()
    future_date = (date.today() + timedelta(days=365)).isoformat()
    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": f"futurebd-{uid}@example.com",
            "first_name": "Paul",
            "last_name": "Futur",
            "role": "employee",
            "birth_date": future_date,
            "address": "5 Avenue Victor Hugo, Lyon",
        },
        headers=_auth(admin),
    )
    assert resp.status_code == 422, resp.text


# ===========================================================================
# 12c.16 — Integration test désactivation différée
# ===========================================================================

@pytest.mark.asyncio
async def test_schedule_deactivation_stores_date(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """PUT /admin/users/{id}/schedule-deactivation → 204, deactivation_scheduled_at stocké en DB."""
    uid = _uid()
    emp = await make_employee(db, email=f"emp-sched-{uid}@example.com", role="employee")
    await db.commit()

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()

    resp = await client.put(
        f"/api/v1/admin/users/{emp.employee_id}/schedule-deactivation",
        json={"scheduled_at": scheduled_at},
        headers=_auth(admin),
    )
    assert resp.status_code == 204, resp.text

    # Vérifier que la date est bien stockée en base — on re-requête par PK sans toucher l'objet ORM
    emp_id = emp.employee_id
    result = await db.execute(
        select(Employee).where(Employee.employee_id == emp_id)
    )
    refreshed = result.scalar_one()
    assert refreshed.deactivation_scheduled_at is not None, \
        "deactivation_scheduled_at doit être stocké après schedule-deactivation"


# ===========================================================================
# 12c.17 — Unit test process_scheduled_deactivations
# ===========================================================================

@pytest.mark.asyncio
async def test_process_scheduled_deactivations_past_date_deactivates(db: AsyncSession):
    """Employé avec deactivation_scheduled_at dans le passé → désactivé par la tâche."""
    from app.tasks.deactivation_tasks import _deactivate_due_employees

    uid = _uid()
    emp = await make_employee(db, email=f"emp-past-{uid}@example.com", role="employee")
    # Planifier une désactivation dans le passé
    past_date = datetime.now(timezone.utc) - timedelta(hours=1)
    emp.deactivation_scheduled_at = past_date
    await db.flush()
    await db.commit()

    # Exécuter la logique directement avec la session de test (sans Celery ni Postgres)
    count = await _deactivate_due_employees(db)
    assert count >= 1, f"Au moins 1 employé devrait être désactivé, got {count}"

    # Vérifier que l'employé est maintenant inactif
    result = await db.execute(
        select(Employee).where(Employee.employee_id == emp.employee_id)
    )
    refreshed = result.scalar_one()
    assert refreshed.employment_status == "inactive", \
        "L'employé avec une date passée doit être désactivé"
    assert refreshed.deactivation_scheduled_at is None, \
        "deactivation_scheduled_at doit être effacé après désactivation"


@pytest.mark.asyncio
async def test_process_scheduled_deactivations_future_date_ignored(db: AsyncSession):
    """Employé avec deactivation_scheduled_at dans le futur → non désactivé par la tâche."""
    from app.tasks.deactivation_tasks import _deactivate_due_employees

    uid = _uid()
    emp = await make_employee(db, email=f"emp-future-{uid}@example.com", role="employee")
    # Planifier une désactivation dans le futur
    future_date = datetime.now(timezone.utc) + timedelta(days=30)
    emp.deactivation_scheduled_at = future_date
    await db.flush()
    await db.commit()

    # Exécuter la logique
    await _deactivate_due_employees(db)

    # Vérifier que l'employé est toujours actif
    result = await db.execute(
        select(Employee).where(Employee.employee_id == emp.employee_id)
    )
    refreshed = result.scalar_one()
    assert refreshed.employment_status == "active", \
        "L'employé avec une date future ne doit PAS être désactivé"
    assert refreshed.deactivation_scheduled_at is not None, \
        "deactivation_scheduled_at doit rester intact pour une date future"
