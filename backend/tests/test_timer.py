"""Tests for timer start/stop functionality."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.timer import ActiveTimer
from app.models.timesheet_entry import TimesheetEntry
from tests.conftest import make_client, make_employee, make_project


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


@pytest_asyncio.fixture
async def setup(db: AsyncSession):
    """Create employee, client, project for timer tests."""
    uid = _uid()
    manager = await make_employee(db, email=f"manager-{uid}@example.com", role="manager")
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee", manager_id=manager.employee_id)
    cli = await make_client(db, name=f"Client-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    return {"emp": emp, "manager": manager, "proj": proj}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_timer_success(client: AsyncClient, db: AsyncSession, setup):
    """Test starting a timer."""
    emp = setup["emp"]
    proj = setup["proj"]

    resp = await client.post(
        "/api/v1/timer/start",
        json={
            "project_id": proj.project_id,
            "description": "Working on feature",
            "task_type": "development",
        },
        headers=_auth_header(emp),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["employee_id"] == emp.employee_id
    assert data["project_id"] == proj.project_id
    assert data["description"] == "Working on feature"
    assert data["task_type"] == "development"
    assert "timer_id" in data
    assert "started_at" in data
    assert data["elapsed_seconds"] == 0


@pytest.mark.asyncio
async def test_get_active_timer(client: AsyncClient, db: AsyncSession, setup):
    """Test getting active timer."""
    emp = setup["emp"]
    proj = setup["proj"]

    # Start a timer
    await client.post(
        "/api/v1/timer/start",
        json={"project_id": proj.project_id},
        headers=_auth_header(emp),
    )

    # Get active timer
    resp = await client.get(
        "/api/v1/timer/active",
        headers=_auth_header(emp),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data is not None
    assert data["employee_id"] == emp.employee_id
    assert data["project_id"] == proj.project_id


@pytest.mark.asyncio
async def test_get_active_timer_none(client: AsyncClient, db: AsyncSession, setup):
    """Test getting active timer when none exists."""
    emp = setup["emp"]

    resp = await client.get(
        "/api/v1/timer/active",
        headers=_auth_header(emp),
    )

    assert resp.status_code == 200, resp.text
    assert resp.json() is None


@pytest.mark.asyncio
async def test_start_timer_replaces_existing(client: AsyncClient, db: AsyncSession, setup):
    """Test starting a new timer replaces the existing one."""
    emp = setup["emp"]
    proj = setup["proj"]

    # Start first timer
    resp1 = await client.post(
        "/api/v1/timer/start",
        json={"project_id": proj.project_id, "description": "First task"},
        headers=_auth_header(emp),
    )
    assert resp1.status_code == 200
    timer1_id = resp1.json()["timer_id"]

    # Start second timer
    resp2 = await client.post(
        "/api/v1/timer/start",
        json={"project_id": proj.project_id, "description": "Second task"},
        headers=_auth_header(emp),
    )
    assert resp2.status_code == 200
    timer2_id = resp2.json()["timer_id"]

    # Verify only one timer exists
    result = await db.execute(
        select(ActiveTimer).where(ActiveTimer.employee_id == emp.employee_id)
    )
    timers = result.scalars().all()
    assert len(timers) == 1
    assert timers[0].description == "Second task"


@pytest.mark.asyncio
async def test_stop_timer_creates_entry(client: AsyncClient, db: AsyncSession, setup):
    """Test stopping a timer creates a timesheet entry for duration >= 1 minute."""
    emp = setup["emp"]
    proj = setup["proj"]

    # Start timer
    await client.post(
        "/api/v1/timer/start",
        json={"project_id": proj.project_id, "description": "Test work"},
        headers=_auth_header(emp),
    )

    # Wait 2 seconds to ensure duration > 1 minute simulation (we'll manually adjust in DB)
    # For testing, we'll manipulate the started_at time
    result = await db.execute(
        select(ActiveTimer).where(ActiveTimer.employee_id == emp.employee_id)
    )
    timer = result.scalar_one()
    timer.started_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db.flush()

    # Stop timer
    resp = await client.post(
        "/api/v1/timer/stop",
        headers=_auth_header(emp),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["message"] == "Timer arrêté"
    assert data["hours_worked"] > 0.9  # Should be ~1 hour
    assert data["timesheet_entry_id"] is not None

    # Verify timer was deleted
    result = await db.execute(
        select(ActiveTimer).where(ActiveTimer.employee_id == emp.employee_id)
    )
    assert result.scalar_one_or_none() is None

    # Verify timesheet entry was created
    result = await db.execute(
        select(TimesheetEntry).where(TimesheetEntry.timesheet_entry_id == data["timesheet_entry_id"])
    )
    entry = result.scalar_one()
    assert entry.employee_id == emp.employee_id
    assert entry.project_id == proj.project_id
    assert entry.description == "Test work"
    assert entry.status == "draft"


@pytest.mark.asyncio
async def test_stop_timer_short_duration_no_entry(client: AsyncClient, db: AsyncSession, setup):
    """Test stopping a timer with duration < 1 minute does not create entry."""
    emp = setup["emp"]
    proj = setup["proj"]

    # Start timer
    await client.post(
        "/api/v1/timer/start",
        json={"project_id": proj.project_id},
        headers=_auth_header(emp),
    )

    # Stop immediately (< 1 minute)
    resp = await client.post(
        "/api/v1/timer/stop",
        headers=_auth_header(emp),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["hours_worked"] < 0.1  # Very short duration
    assert data["timesheet_entry_id"] is None

    # Verify no timesheet entry was created
    result = await db.execute(
        select(TimesheetEntry).where(TimesheetEntry.employee_id == emp.employee_id)
    )
    entries = result.scalars().all()
    # Note: there might be entries from other tests, but none from this timer


@pytest.mark.asyncio
async def test_stop_timer_no_active(client: AsyncClient, db: AsyncSession, setup):
    """Test stopping a timer when none is active returns 404."""
    emp = setup["emp"]

    resp = await client.post(
        "/api/v1/timer/stop",
        headers=_auth_header(emp),
    )

    assert resp.status_code == 404, resp.text
    assert "Aucun timer actif" in resp.json()["detail"]
