"""Tests for timesheet entry CRUD, submit_week, and RBAC."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_client, make_employee, make_entry, make_project
from app.core.security import create_access_token


def _uid() -> str:
    """Short unique suffix to avoid email collisions across tests."""
    return uuid.uuid4().hex[:8]


def _auth_header(employee) -> dict:
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
async def setup(db: AsyncSession):
    """Create employee, client, project for timesheet tests."""
    uid = _uid()
    manager = await make_employee(db, email=f"manager-{uid}@example.com", role="manager")
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee", manager_id=manager.employee_id)
    cli = await make_client(db, name=f"Client-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    # Add emp to team_members
    from app.repositories.project_repository import ProjectRepository
    repo = ProjectRepository(db)
    await repo.update(proj.project_id, team_members=[manager.employee_id, emp.employee_id])
    # Ensure OrgSettings with max_hours_per_day=16 for tests
    from app.models.org_settings import OrgSettings
    from sqlalchemy import select as _sel
    result = await db.execute(_sel(OrgSettings).where(OrgSettings.org_id == 1))
    org = result.scalar_one_or_none()
    if not org:
        from decimal import Decimal
        org = OrgSettings(
            org_id=1,
            standard_hours_per_day=Decimal("8"),
            max_hours_per_day=Decimal("16"),
        )
        db.add(org)
    else:
        from decimal import Decimal
        org.max_hours_per_day = Decimal("16")
    await db.flush()
    await db.refresh(proj)
    return {"emp": emp, "manager": manager, "proj": proj, "uid": uid}


# ---------------------------------------------------------------------------
# 2.22 — create_entry validation paths
# ---------------------------------------------------------------------------

async def test_create_entry_success(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    today = date.today()
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": proj.project_id,
            "work_date": str(today),
            "hours_worked": "8.0",
            "description": "Worked on feature",
            "task_type": "dev",
        },
        headers=_auth_header(emp),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["hours_worked"] == 8.0
    assert data["status"] == "draft"


async def test_create_entry_invalid_hours_zero(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": proj.project_id,
            "work_date": str(date.today()),
            "hours_worked": "0",
            "description": "Zero hours",
            "task_type": "dev",
        },
        headers=_auth_header(emp),
    )
    assert resp.status_code == 422


async def test_create_entry_invalid_hours_too_many(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": proj.project_id,
            "work_date": str(date.today()),
            "hours_worked": "17",
            "description": "Too many hours",
            "task_type": "dev",
        },
        headers=_auth_header(emp),
    )
    assert resp.status_code == 422


async def test_create_entry_future_date(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    future = date.today() + timedelta(days=1)
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": proj.project_id,
            "work_date": str(future),
            "hours_worked": "8.0",
            "description": "Future entry",
            "task_type": "dev",
        },
        headers=_auth_header(emp),
    )
    assert resp.status_code == 422


async def test_create_entry_duplicate(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    today = date.today()
    payload = {
        "project_id": proj.project_id,
        "work_date": str(today),
        "hours_worked": "4.0",
        "description": "First entry",
        "task_type": "dev",
    }
    r1 = await client.post("/api/v1/employee/timesheet/entries", json=payload, headers=_auth_header(emp))
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/employee/timesheet/entries", json=payload, headers=_auth_header(emp))
    assert r2.status_code == 409


async def test_create_entry_daily_max_exceeded(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    uid = setup["uid"]
    cli2 = await make_client(db, name=f"Second-{uid}")
    proj2 = await make_project(db, client_id=cli2.client_id, manager_id=setup["manager"].employee_id)
    from app.repositories.project_repository import ProjectRepository
    await ProjectRepository(db).update(proj2.project_id, team_members=[emp.employee_id])
    await db.flush()

    today = date.today()
    # First entry: 10 hours on proj
    r1 = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={"project_id": proj.project_id, "work_date": str(today), "hours_worked": "10.0", "description": "A", "task_type": "dev"},
        headers=_auth_header(emp),
    )
    assert r1.status_code == 201
    # Second entry: 7 hours on proj2 — total would be 17
    r2 = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={"project_id": proj2.project_id, "work_date": str(today), "hours_worked": "7.0", "description": "B", "task_type": "dev"},
        headers=_auth_header(emp),
    )
    assert r2.status_code == 422


async def test_create_entry_inactive_project(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    uid = setup["uid"]
    cli = await make_client(db, name=f"InactiveCli-{uid}")
    inactive_proj = await make_project(
        db, client_id=cli.client_id, manager_id=setup["manager"].employee_id, status="inactive"
    )
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": inactive_proj.project_id,
            "work_date": str(date.today()),
            "hours_worked": "4.0",
            "description": "Inactive project",
            "task_type": "dev",
        },
        headers=_auth_header(emp),
    )
    assert resp.status_code == 422


async def test_create_entry_draft_project_returns_422(client: AsyncClient, db: AsyncSession, setup):
    """Spec 12c.36 — saisie sur projet en statut draft → 422."""
    emp = setup["emp"]
    uid = setup["uid"]
    cli = await make_client(db, name=f"DraftCli-{uid}")
    draft_proj = await make_project(
        db, client_id=cli.client_id, manager_id=setup["manager"].employee_id, status="draft"
    )
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": draft_proj.project_id,
            "work_date": str(date.today()),
            "hours_worked": "4.0",
            "description": "Draft project entry",
            "task_type": "dev",
        },
        headers=_auth_header(emp),
    )
    assert resp.status_code == 422, resp.text
    assert "actif" in resp.json().get("detail", "").lower() or "active" in resp.json().get("detail", "").lower()


# ---------------------------------------------------------------------------
# 2.23 — submit_week
# ---------------------------------------------------------------------------

async def test_submit_week_no_entries(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    resp = await client.post(
        "/api/v1/employee/timesheet/submit",
        json={"week": "2020-W01"},
        headers=_auth_header(emp),
    )
    assert resp.status_code == 400


async def test_submit_week_already_submitted(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    # Use a unique week far in the past to avoid collision with other tests
    work_date = date(2021, 1, 4)  # Week 2021-W01 Monday
    await make_entry(db, emp.employee_id, proj.project_id, work_date, hours=8.0)
    await db.commit()

    r1 = await client.post(
        "/api/v1/employee/timesheet/submit",
        json={"week": "2021-W01"},
        headers=_auth_header(emp),
    )
    assert r1.status_code == 200

    # Re-create a draft entry for same week (simulate new draft after submit)
    # Actually the week is already submitted — just try submitting again
    r2 = await client.post(
        "/api/v1/employee/timesheet/submit",
        json={"week": "2021-W01"},
        headers=_auth_header(emp),
    )
    assert r2.status_code in (400, 409)


async def test_submit_week_success(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]
    work_date = date(2022, 3, 7)  # Week 2022-W10 Monday
    await make_entry(db, emp.employee_id, proj.project_id, work_date, hours=6.0)
    await db.commit()

    resp = await client.post(
        "/api/v1/employee/timesheet/submit",
        json={"week": "2022-W10"},
        headers=_auth_header(emp),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "submitted"
    assert data["entries_submitted"] == 1

    # Verify entries are now 'submitted'
    week_resp = await client.get(
        "/api/v1/employee/timesheet/week?week=2022-W10",
        headers=_auth_header(emp),
    )
    assert week_resp.status_code == 200
    week_data = week_resp.json()
    all_entries = [e for day_entries in week_data["entries"].values() for e in day_entries]
    assert all(e["status"] == "submitted" for e in all_entries)


# ---------------------------------------------------------------------------
# 2.24 — Integration: full create → submit flow
# ---------------------------------------------------------------------------

async def test_full_week_flow(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    proj = setup["proj"]

    # Create entries Mon–Wed of a unique week
    week = "2023-W15"
    dates = [date(2023, 4, 10), date(2023, 4, 11), date(2023, 4, 12)]
    for d in dates:
        r = await client.post(
            "/api/v1/employee/timesheet/entries",
            json={
                "project_id": proj.project_id,
                "work_date": str(d),
                "hours_worked": "8.0",
                "description": f"Work on {d}",
                "task_type": "dev",
            },
            headers=_auth_header(emp),
        )
        assert r.status_code == 201

    # Verify week view
    week_resp = await client.get(f"/api/v1/employee/timesheet/week?week={week}", headers=_auth_header(emp))
    assert week_resp.status_code == 200
    week_data = week_resp.json()
    assert week_data["week_total"] == 24.0

    # Submit
    submit_resp = await client.post(
        "/api/v1/employee/timesheet/submit",
        json={"week": week},
        headers=_auth_header(emp),
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["entries_submitted"] == 3

    # Verify approval created via DB
    from app.repositories.timesheet_repository import TimesheetRepository
    repo = TimesheetRepository(db)
    approval = await repo.get_approval_for_week(emp.employee_id, date(2023, 4, 10))
    assert approval is not None
    assert approval.status == "pending"


# ---------------------------------------------------------------------------
# 2.25 — RBAC: employee cannot access admin/clients
# ---------------------------------------------------------------------------

async def test_employee_cannot_access_admin_clients(client: AsyncClient, db: AsyncSession, setup):
    emp = setup["emp"]
    resp = await client.post(
        "/api/v1/admin/clients",
        json={
            "client_name": "Hack Corp",
            "email": "hack@example.com",
            "default_billing_rate": "100.00",
        },
        headers=_auth_header(emp),
    )
    assert resp.status_code == 403
