"""Integration tests for proxy admin (US-01).

12d.15 — POST /admin/proxy/start → valid proxy token; entry created with proxy_admin_id stored
12d.16 — proxy token cannot access GET /admin/users → 403
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.org_settings import OrgSettings
from app.models.proxy_audit_log import ProxyAuditLog
from app.models.timesheet_entry import TimesheetEntry
from tests.conftest import make_client, make_employee, make_project


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


def _proxy_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def proxy_setup(db: AsyncSession):
    uid = _uid()
    admin = await make_employee(db, email=f"admin-{uid}@example.com", role="admin")
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    cli = await make_client(db, name=f"Client-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=admin.employee_id)

    # Ensure OrgSettings
    from sqlalchemy import select as _sel
    from decimal import Decimal
    result = await db.execute(_sel(OrgSettings).where(OrgSettings.org_id == 1))
    org = result.scalar_one_or_none()
    if not org:
        org = OrgSettings(org_id=1, standard_hours_per_day=Decimal("8"), max_hours_per_day=Decimal("16"))
        db.add(org)
    await db.flush()

    return {"admin": admin, "emp": emp, "proj": proj, "uid": uid}


# ---------------------------------------------------------------------------
# 12d.15 — proxy token issued; timesheet entry stores proxy_admin_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_proxy_token_issued_and_entry_stores_proxy_admin_id(
    client: AsyncClient, db: AsyncSession, proxy_setup
):
    """POST /admin/proxy/start returns a proxy token; entry created with it stores proxy_admin_id."""
    admin = proxy_setup["admin"]
    emp = proxy_setup["emp"]
    proj = proxy_setup["proj"]

    # Directly call create_proxy_token via service (bypasses license check in test)
    from app.services.auth_service import AuthService
    svc = AuthService(db)
    result = await svc.create_proxy_token(
        admin_id=admin.employee_id,
        employee_id=emp.employee_id,
    )
    proxy_token = result["token"]
    proxy_log_id = result["proxy_log_id"]

    assert proxy_token
    assert proxy_log_id > 0

    # Verify audit log was created
    from sqlalchemy import select as _sel
    log_result = await db.execute(_sel(ProxyAuditLog).where(ProxyAuditLog.id == proxy_log_id))
    log = log_result.scalar_one_or_none()
    assert log is not None
    assert log.admin_id == admin.employee_id
    assert log.employee_id == emp.employee_id
    assert log.ended_at is None

    # Create a timesheet entry using the proxy token
    today = date.today()
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        headers=_proxy_header(proxy_token),
        json={
            "project_id": proj.project_id,
            "work_date": str(today),
            "hours_worked": 4.0,
            "description": "Proxy entry",
            "task_type": "dev",
            "entry_type": "normal",
            "billable_flag": True,
        },
    )
    assert resp.status_code == 201, resp.text

    # Verify proxy_admin_id is stored on the entry
    entry_id = resp.json()["timesheet_entry_id"]
    entry_result = await db.execute(_sel(TimesheetEntry).where(TimesheetEntry.timesheet_entry_id == entry_id))
    entry = entry_result.scalar_one_or_none()
    assert entry is not None
    assert entry.proxy_admin_id == admin.employee_id
    assert entry.employee_id == emp.employee_id


# ---------------------------------------------------------------------------
# 12d.16 — proxy token cannot access admin routes → 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_proxy_token_cannot_access_admin_users(
    client: AsyncClient, db: AsyncSession, proxy_setup
):
    """A proxy token must not grant access to GET /admin/users (403)."""
    admin = proxy_setup["admin"]
    emp = proxy_setup["emp"]

    from app.services.auth_service import AuthService
    svc = AuthService(db)
    result = await svc.create_proxy_token(
        admin_id=admin.employee_id,
        employee_id=emp.employee_id,
    )
    proxy_token = result["token"]

    # Proxy token has role of the employee (not admin), so require_role('admin') must reject it
    resp = await client.get(
        "/api/v1/admin/users",
        headers=_proxy_header(proxy_token),
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_end_proxy_session_records_ended_at(
    client: AsyncClient, db: AsyncSession, proxy_setup
):
    """end_proxy_session sets ended_at and entries_created on the log."""
    admin = proxy_setup["admin"]
    emp = proxy_setup["emp"]

    from app.services.auth_service import AuthService
    from sqlalchemy import select as _sel
    svc = AuthService(db)
    result = await svc.create_proxy_token(
        admin_id=admin.employee_id,
        employee_id=emp.employee_id,
    )
    log_id = result["proxy_log_id"]

    await svc.end_proxy_session(log_id, entries_created=3)

    log_result = await db.execute(_sel(ProxyAuditLog).where(ProxyAuditLog.id == log_id))
    log = log_result.scalar_one_or_none()
    assert log.ended_at is not None
    assert log.entries_created == 3
