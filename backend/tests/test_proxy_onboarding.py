"""Tests — spec 12d : Mode Proxy Admin & Onboarding Différé.

Covers:
  12d.30 — create_employee_or_pending :
             hire_date futur (> today + lead_days) → PendingEmployee créé
             hire_date passé / immédiat → Employee créé directement
  12d.31 — activate_pending_employees :
             account_creation_date = today → compte Employee créé, PendingEmployee supprimé
             account_creation_date future → ignoré
  12d.32 — POST /admin/users avec hire_date dans 10 jours et lead_days = 2
             → pending_employee créé avec account_creation_date = hire_date - 2
  12d.15 — POST /admin/proxy/start → token proxy valide
  12d.16 — token proxy ne peut pas accéder aux routes admin → 403
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.org_settings import OrgSettings
from app.models.pending_employee import PendingEmployee
from tests.conftest import make_employee


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _auth(employee: Employee) -> dict:
    """Build Authorization header for a regular employee token."""
    token = create_access_token({
        "sub": employee.email,
        "employee_id": employee.employee_id,
        "org_id": employee.org_id,
        "role": employee.role,
    })
    return {"Authorization": f"Bearer {token}"}


def _proxy_auth(admin: Employee, target: Employee) -> dict:
    """Build Authorization header for a proxy token (admin impersonating target)."""
    token = create_access_token({
        "sub": target.email,
        "employee_id": target.employee_id,
        "org_id": target.org_id,
        "role": target.role,
        "is_proxy": True,
        "proxy_admin_id": admin.employee_id,
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def admin(db: AsyncSession) -> Employee:
    emp = await make_employee(db, email=f"admin-{_uid()}@example.com", role="admin")
    await db.commit()
    return emp


@pytest_asyncio.fixture
async def employee(db: AsyncSession) -> Employee:
    emp = await make_employee(db, email=f"emp-{_uid()}@example.com", role="employee")
    await db.commit()
    return emp


@pytest_asyncio.fixture
async def org_settings_lead2(db: AsyncSession) -> OrgSettings:
    """Ensure org_settings exists with account_creation_lead_days = 2."""
    result = await db.execute(select(OrgSettings).where(OrgSettings.org_id == 1))
    s = result.scalar_one_or_none()
    if s is None:
        from decimal import Decimal
        s = OrgSettings(
            org_id=1,
            org_name="Test Org",
            standard_hours_per_day=Decimal("8"),
            max_hours_per_day=Decimal("24"),
            overtime_rate_multiplier=Decimal("1.25"),
            travel_rate_multiplier=Decimal("0.5"),
            account_creation_lead_days=2,
        )
        db.add(s)
    else:
        s.account_creation_lead_days = 2
    await db.flush()
    await db.commit()
    return s


# ===========================================================================
# 12d.30 — Unit tests : create_employee_or_pending
# ===========================================================================

@pytest.mark.asyncio
async def test_create_employee_or_pending_future_hire(
    db: AsyncSession, org_settings_lead2: OrgSettings
):
    """hire_date suffisamment futur → PendingEmployee créé (type='pending')."""
    from app.services.auth_service import AuthService

    uid = _uid()
    # hire_date dans 10 jours → account_creation_date = today + 8 > today → deferred
    hire_date = date.today() + timedelta(days=10)

    svc = AuthService(db)
    result = await svc.create_employee_or_pending(
        email=f"pending-{uid}@example.com",
        first_name="Marie",
        last_name="Futur",
        role="employee",
        birth_date=date(1990, 5, 15),
        address="12 Rue de la Paix, Paris",
        hire_date=hire_date,
    )

    assert result["type"] == "pending", f"Expected 'pending', got {result['type']!r}"
    assert "account_creation_date" in result
    assert "id" in result

    # Vérifier que le PendingEmployee est bien en base
    pending_id = result["id"]
    db_result = await db.execute(
        select(PendingEmployee).where(PendingEmployee.id == pending_id)
    )
    pending = db_result.scalar_one_or_none()
    assert pending is not None, "PendingEmployee doit exister en base"
    assert pending.hire_date == hire_date

    # account_creation_date = hire_date - lead_days (2)
    expected_creation = hire_date - timedelta(days=2)
    assert pending.account_creation_date == expected_creation, (
        f"account_creation_date attendu {expected_creation}, got {pending.account_creation_date}"
    )


@pytest.mark.asyncio
async def test_create_employee_or_pending_past_hire(
    db: AsyncSession, org_settings_lead2: OrgSettings
):
    """hire_date passé ou immédiat → Employee créé directement (type='employee')."""
    from app.services.auth_service import AuthService

    uid = _uid()
    # hire_date = aujourd'hui → account_creation_date = today - 2 ≤ today → immédiat
    hire_date = date.today()

    svc = AuthService(db)
    result = await svc.create_employee_or_pending(
        email=f"immediate-{uid}@example.com",
        first_name="Paul",
        last_name="Immédiat",
        role="employee",
        birth_date=date(1988, 3, 20),
        address="5 Avenue Victor Hugo, Lyon",
        hire_date=hire_date,
    )

    assert result["type"] == "employee", f"Expected 'employee', got {result['type']!r}"
    assert "id" in result

    # Vérifier que l'Employee est bien en base
    emp_id = result["id"]
    db_result = await db.execute(
        select(Employee).where(Employee.employee_id == emp_id)
    )
    emp = db_result.scalar_one_or_none()
    assert emp is not None, "Employee doit exister en base"
    assert emp.employment_status == "active"


@pytest.mark.asyncio
async def test_create_employee_or_pending_no_hire_date(
    db: AsyncSession, org_settings_lead2: OrgSettings
):
    """Sans hire_date → Employee créé immédiatement."""
    from app.services.auth_service import AuthService

    uid = _uid()
    svc = AuthService(db)
    result = await svc.create_employee_or_pending(
        email=f"nohire-{uid}@example.com",
        first_name="Alice",
        last_name="NoHire",
        role="employee",
        birth_date=date(1992, 7, 10),
        address="3 Rue du Commerce, Bordeaux",
        hire_date=None,
    )

    assert result["type"] == "employee", f"Expected 'employee', got {result['type']!r}"


# ===========================================================================
# 12d.31 — Unit tests : activate_pending_employees (logique interne)
# ===========================================================================

@pytest.mark.asyncio
async def test_activate_pending_due_today(db: AsyncSession, org_settings_lead2: OrgSettings):
    """account_creation_date = today → Employee créé, PendingEmployee supprimé."""
    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    from app.services.auth_service import AuthService

    uid = _uid()
    today = date.today()

    # Créer un PendingEmployee dont account_creation_date = today
    repo = PendingEmployeeRepository(db)
    pending = await repo.create(
        first_name="Jean",
        last_name="DueToday",
        email=f"due-today-{uid}@example.com",
        role="employee",
        hire_date=today + timedelta(days=2),
        account_creation_date=today,
        birth_date=date(1991, 4, 12),
        address="8 Boulevard Haussmann, Paris",
    )
    await db.commit()
    pending_id = pending.id

    # Simuler la logique de la tâche Celery directement
    due = await repo.get_pending_due(today)
    assert any(p.id == pending_id for p in due), "Le pending doit être dans la liste due"

    svc = AuthService(db)
    employee = await svc.create_employee(
        email=pending.email,
        first_name=pending.first_name,
        last_name=pending.last_name,
        role=pending.role,
        birth_date=pending.birth_date,
        address=pending.address,
    )
    await repo.delete(pending_id)
    await db.commit()

    # Vérifier que l'Employee existe
    emp_result = await db.execute(
        select(Employee).where(Employee.employee_id == employee.employee_id)
    )
    assert emp_result.scalar_one_or_none() is not None, "Employee doit être créé"

    # Vérifier que le PendingEmployee est supprimé
    pending_result = await db.execute(
        select(PendingEmployee).where(PendingEmployee.id == pending_id)
    )
    assert pending_result.scalar_one_or_none() is None, "PendingEmployee doit être supprimé"


@pytest.mark.asyncio
async def test_activate_pending_future_date_ignored(db: AsyncSession):
    """account_creation_date dans le futur → non retourné par get_pending_due."""
    from app.repositories.pending_employee_repository import PendingEmployeeRepository

    uid = _uid()
    today = date.today()
    future_date = today + timedelta(days=5)

    repo = PendingEmployeeRepository(db)
    pending = await repo.create(
        first_name="Futur",
        last_name="NotYet",
        email=f"future-{uid}@example.com",
        role="employee",
        hire_date=future_date + timedelta(days=2),
        account_creation_date=future_date,
    )
    await db.commit()

    due = await repo.get_pending_due(today)
    assert not any(p.id == pending.id for p in due), (
        "Un pending avec account_creation_date future ne doit PAS être dans la liste due"
    )


# ===========================================================================
# 12d.32 — Integration test : POST /admin/users avec hire_date futur
# ===========================================================================

@pytest.mark.asyncio
async def test_post_admin_users_future_hire_creates_pending(
    client: AsyncClient, db: AsyncSession, admin: Employee, org_settings_lead2: OrgSettings
):
    """POST /admin/users avec hire_date dans 10 jours et lead_days=2
    → pending_employee créé avec account_creation_date = hire_date - 2."""
    uid = _uid()
    hire_date = date.today() + timedelta(days=10)
    expected_creation = hire_date - timedelta(days=2)

    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": f"hire-future-{uid}@example.com",
            "first_name": "Nouveau",
            "last_name": "Recrue",
            "role": "employee",
            "birth_date": "1995-06-20",
            "address": "21 Rue de Rivoli, Paris",
            "hire_date": hire_date.isoformat(),
        },
        headers=_auth(admin),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["type"] == "pending", f"Expected type='pending', got {data.get('type')!r}"
    assert "account_creation_date" in data, "account_creation_date doit être dans la réponse"
    assert data["account_creation_date"] == expected_creation.isoformat(), (
        f"account_creation_date attendu {expected_creation.isoformat()}, "
        f"got {data['account_creation_date']!r}"
    )

    # Vérifier en base
    result = await db.execute(
        select(PendingEmployee).where(PendingEmployee.email == f"hire-future-{uid}@example.com")
    )
    pending = result.scalar_one_or_none()
    assert pending is not None, "PendingEmployee doit exister en base"
    assert pending.account_creation_date == expected_creation


# ===========================================================================
# 12d.15 — Integration test : POST /admin/proxy/start → token proxy valide
# ===========================================================================

@pytest.mark.asyncio
async def test_proxy_start_returns_token(
    client: AsyncClient, db: AsyncSession, admin: Employee, employee: Employee
):
    """POST /admin/proxy/start → retourne un token proxy valide avec proxy_log_id."""
    # Activer la licence Finance Pro avec une clé valide générée dynamiquement
    from app.models.module_license import ModuleLicense
    from app.utils.module_license import generate_key
    from datetime import date as _date

    valid_key = generate_key(expiry=_date(2099, 12, 31))
    expiry = _date(2099, 12, 31)

    result = await db.execute(
        select(ModuleLicense).where(
            ModuleLicense.org_id == 1,
            ModuleLicense.module_name == "finance_pro",
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.license_key = valid_key
        existing.expires_at = expiry
    else:
        lic = ModuleLicense(
            org_id=1,
            module_name="finance_pro",
            license_key=valid_key,
            expires_at=expiry,
        )
        db.add(lic)
    await db.commit()

    resp = await client.post(
        "/api/v1/admin/proxy/start",
        json={"employee_id": employee.employee_id},
        headers=_auth(admin),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "token" in data, "La réponse doit contenir un token"
    assert "proxy_log_id" in data, "La réponse doit contenir un proxy_log_id"
    assert isinstance(data["proxy_log_id"], int)

    # Décoder le token et vérifier les claims proxy
    from app.core.security import decode_access_token
    payload = decode_access_token(data["token"])
    assert payload.get("is_proxy") is True, "Le token doit avoir is_proxy=True"
    assert payload.get("proxy_admin_id") == admin.employee_id, (
        f"proxy_admin_id attendu {admin.employee_id}, got {payload.get('proxy_admin_id')}"
    )
    assert payload.get("employee_id") == employee.employee_id, (
        f"employee_id attendu {employee.employee_id}, got {payload.get('employee_id')}"
    )


# ===========================================================================
# 12d.16 — Integration test : token proxy ne peut pas accéder aux routes admin
# ===========================================================================

@pytest.mark.asyncio
async def test_proxy_token_cannot_access_admin_routes(
    client: AsyncClient, db: AsyncSession, admin: Employee, employee: Employee
):
    """Un token proxy (is_proxy=True, role=employee) ne peut pas accéder à GET /admin/users → 403."""
    proxy_headers = _proxy_auth(admin, employee)

    resp = await client.get("/api/v1/admin/users", headers=proxy_headers)
    assert resp.status_code == 403, (
        f"Un token proxy avec role=employee doit recevoir 403 sur les routes admin, "
        f"got {resp.status_code}: {resp.text}"
    )


@pytest.mark.asyncio
async def test_proxy_token_can_access_timesheet(
    client: AsyncClient, db: AsyncSession, admin: Employee, employee: Employee
):
    """Un token proxy peut accéder aux routes timesheet de l'employé impersonné."""
    from tests.conftest import make_client, make_project

    # Créer un projet actif pour la saisie
    c = await make_client(db)
    p = await make_project(db, client_id=c.client_id, manager_id=admin.employee_id)
    await db.commit()

    proxy_headers = _proxy_auth(admin, employee)

    # GET /timesheet/week doit fonctionner avec un token proxy
    resp = await client.get(
        "/api/v1/timesheet/week?week=2026-W01",
        headers=proxy_headers,
    )
    # 200 ou 404 (semaine sans entrées) sont acceptables — l'important est que ce n'est pas 403
    assert resp.status_code in (200, 404, 422), (
        f"Token proxy doit pouvoir accéder au timesheet, got {resp.status_code}: {resp.text}"
    )
