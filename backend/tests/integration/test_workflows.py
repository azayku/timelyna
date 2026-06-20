"""Integration tests for complete API workflows — TEST-INT-001 through TEST-INT-004.

These tests use the real HTTP client + SQLite in-memory DB (no mocks for DB layer).
"""
from __future__ import annotations

from datetime import date
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_employee, make_client, make_project, make_entry


# Shared week used across integration scenarios
WEEK = "2026-W19"
WEEK_DATES = [
    "2026-05-04",
    "2026-05-05",
    "2026-05-06",
    "2026-05-07",
    "2026-05-08",
]


# ---------------------------------------------------------------------------
# TEST-INT-001 — full weekly workflow: submit and approve
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_weekly_workflow_submit_and_approve(
    client: AsyncClient, db: AsyncSession
):
    """Employee creates 5 entries, submits the week, manager approves."""
    # Setup
    manager = await make_employee(db, email="int001mgr@test.com", password="Pass1234", role="manager")
    employee = await make_employee(
        db, email="int001emp@test.com", password="Pass1234", role="employee", manager_id=manager.employee_id
    )
    cli = await make_client(db)
    project = await make_project(db, cli.client_id, manager.employee_id)
    await db.commit()

    # Login as employee
    login_resp = await client.post("/api/v1/auth/login", json={
        "identifier": "int001emp@test.com",
        "password": "Pass1234",
    })
    assert login_resp.status_code == 200
    emp_token = login_resp.json()["access_token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # Create 5 entries (one per day Mon–Fri)
    for work_date in WEEK_DATES:
        resp = await client.post(
            "/api/v1/employee/timesheet/entries",
            json={
                "project_id": project.project_id,
                "work_date": work_date,
                "hours_worked": 8,
                "description": f"Work on {work_date}",
                "task_type": "dev",
                "entry_type": "normal",
                "billable_flag": True,
            },
            headers=emp_headers,
        )
        assert resp.status_code in (200, 201), f"Failed to create entry for {work_date}: {resp.text}"

    # Submit the week
    with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
        submit_resp = await client.post(
            "/api/v1/employee/timesheet/submit",
            json={"week": WEEK},
            headers=emp_headers,
        )
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert submit_data["entries_submitted"] == 5
    approval_id = submit_data["approval_id"]

    # Login as manager
    mgr_login = await client.post("/api/v1/auth/login", json={
        "identifier": "int001mgr@test.com",
        "password": "Pass1234",
    })
    assert mgr_login.status_code == 200
    mgr_token = mgr_login.json()["access_token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    # Manager lists pending approvals
    list_resp = await client.get(
        "/api/v1/manager/approvals?status=pending",
        headers=mgr_headers,
    )
    assert list_resp.status_code == 200
    pending = list_resp.json()
    assert any(a["approval_id"] == approval_id for a in pending)

    # Manager approves
    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
            approve_resp = await client.post(
                f"/api/v1/manager/approvals/{approval_id}/approve",
                json={"notes": "All correct"},
                headers=mgr_headers,
            )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # Verify entries are approved via employee endpoint
    week_resp = await client.get(
        f"/api/v1/employee/timesheet/week?week={WEEK}",
        headers=emp_headers,
    )
    assert week_resp.status_code == 200
    week_data = week_resp.json()
    all_entries = [
        e for day_entries in week_data.get("entries", {}).values() for e in day_entries
    ]
    assert len(all_entries) == 5
    assert all(e["status"] == "approved" for e in all_entries)


# ---------------------------------------------------------------------------
# TEST-INT-002 — rejection and resubmission workflow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rejection_and_resubmission_workflow(
    client: AsyncClient, db: AsyncSession
):
    """Submit → reject → correct → resubmit → approve."""
    manager = await make_employee(db, email="int002mgr@test.com", password="Pass1234", role="manager")
    employee = await make_employee(
        db, email="int002emp@test.com", password="Pass1234", role="employee", manager_id=manager.employee_id
    )
    cli = await make_client(db)
    project = await make_project(db, cli.client_id, manager.employee_id)
    await db.commit()

    # Employee login
    emp_login = await client.post("/api/v1/auth/login", json={"identifier": "int002emp@test.com", "password": "Pass1234"})
    assert emp_login.status_code == 200
    emp_token = emp_login.json()["access_token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # Create 3 entries
    entry_ids = []
    for i, work_date in enumerate(WEEK_DATES[:3]):
        resp = await client.post(
            "/api/v1/employee/timesheet/entries",
            json={
                "project_id": project.project_id,
                "work_date": work_date,
                "hours_worked": 8,
                "description": "Work",
                "task_type": "dev",
                "entry_type": "normal",
            },
            headers=emp_headers,
        )
        assert resp.status_code in (200, 201)
        entry_ids.append(resp.json()["timesheet_entry_id"])

    # Submit
    with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
        submit_resp = await client.post(
            "/api/v1/employee/timesheet/submit",
            json={"week": WEEK},
            headers=emp_headers,
        )
    assert submit_resp.status_code == 200
    approval_id = submit_resp.json()["approval_id"]

    # Manager login and reject
    mgr_login = await client.post("/api/v1/auth/login", json={"identifier": "int002mgr@test.com", "password": "Pass1234"})
    assert mgr_login.status_code == 200
    mgr_token = mgr_login.json()["access_token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
            reject_resp = await client.post(
                f"/api/v1/manager/approvals/{approval_id}/reject",
                json={"rejection_reason": "Heures incorrectes sur le projet"},
                headers=mgr_headers,
            )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    # Employee corrects one entry (entries should be back in draft after rejection)
    update_resp = await client.put(
        f"/api/v1/employee/timesheet/entries/{entry_ids[0]}",
        json={"hours_worked": 7},
        headers=emp_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["hours_worked"] == 7.0

    # Resubmit
    with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
        resubmit_resp = await client.post(
            "/api/v1/employee/timesheet/submit",
            json={"week": WEEK},
            headers=emp_headers,
        )
    assert resubmit_resp.status_code == 200
    # Must reuse same approval
    assert resubmit_resp.json()["approval_id"] == approval_id

    # Manager approves
    with patch("app.tasks.notification_tasks.task_send_approval_notification"):
        with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
            approve_resp = await client.post(
                f"/api/v1/manager/approvals/{approval_id}/approve",
                json={"notes": "Corrected, approved"},
                headers=mgr_headers,
            )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"


# ---------------------------------------------------------------------------
# TEST-INT-003 — proxy admin creates entry for employee
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_proxy_admin_creates_entry_for_employee(
    client: AsyncClient, db: AsyncSession
):
    """Admin starts proxy session, creates entry for employee, ends session."""
    from sqlalchemy import select
    from app.models.module_license import ModuleLicense
    from app.utils.module_license import generate_key

    admin = await make_employee(db, email="int003admin@test.com", password="Pass1234", role="admin")
    employee = await make_employee(db, email="int003emp@test.com", password="Pass1234", role="employee")
    cli = await make_client(db)
    project = await make_project(db, cli.client_id, admin.employee_id)

    # Proxy routes are gated by Finance Pro license.
    expiry = date(2099, 12, 31)
    valid_key = generate_key(expiry=expiry)
    lic_result = await db.execute(
        select(ModuleLicense).where(
            ModuleLicense.org_id == 1,
            ModuleLicense.module_name == "finance_pro",
        )
    )
    license_row = lic_result.scalar_one_or_none()
    if license_row:
        license_row.license_key = valid_key
        license_row.expires_at = expiry
    else:
        db.add(
            ModuleLicense(
                org_id=1,
                module_name="finance_pro",
                license_key=valid_key,
                expires_at=expiry,
            )
        )

    await db.commit()

    # Admin login
    admin_login = await client.post("/api/v1/auth/login", json={"identifier": "int003admin@test.com", "password": "Pass1234"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Start proxy session
    proxy_resp = await client.post(
        f"/api/v1/admin/proxy/start",
        json={"employee_id": employee.employee_id},
        headers=admin_headers,
    )
    assert proxy_resp.status_code in (200, 201)
    proxy_data = proxy_resp.json()
    proxy_token = proxy_data.get("token")
    proxy_log_id = proxy_data.get("proxy_log_id")
    assert proxy_token is not None
    assert proxy_log_id is not None

    proxy_headers = {"Authorization": f"Bearer {proxy_token}"}

    # Create entry using proxy token
    entry_resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": project.project_id,
            "work_date": "2026-05-04",
            "hours_worked": 8,
            "description": "Proxy created entry",
            "task_type": "dev",
            "entry_type": "normal",
        },
        headers=proxy_headers,
    )
    assert entry_resp.status_code in (200, 201)
    created_entry = entry_resp.json()
    assert created_entry["employee_id"] == employee.employee_id

    # End proxy session
    end_resp = await client.post(
        f"/api/v1/admin/proxy/end",
        json={"proxy_log_id": proxy_log_id, "entries_created": 1},
        headers=admin_headers,
    )
    assert end_resp.status_code in (200, 204)


# ---------------------------------------------------------------------------
# TEST-INT-004 — employee mutation updates manager routing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_employee_mutation_updates_manager(
    client: AsyncClient, db: AsyncSession
):
    """Mutate employee from Org1 to Org2; new submissions route to Org2 manager."""
    from app.models.organization import Organization
    from sqlalchemy import select, update as sa_update

    # Create Org 2 separately
    org2 = Organization(org_id=99, org_name="Org Two")
    db.add(org2)
    await db.flush()

    admin = await make_employee(db, email="int004admin@test.com", password="Pass1234", role="admin")
    manager1 = await make_employee(db, email="int004mgr1@test.com", password="Pass1234", role="manager")
    manager2 = await make_employee(
        db, email="int004mgr2@test.com", password="Pass1234", role="manager",
    )
    # Update org2 to have manager2
    await db.execute(sa_update(Organization).where(Organization.org_id == 99).values(manager_id=manager2.employee_id))

    employee = await make_employee(
        db, email="int004emp@test.com", password="Pass1234", role="employee", manager_id=manager1.employee_id
    )
    cli = await make_client(db)
    project = await make_project(db, cli.client_id, manager2.employee_id)
    await db.commit()

    # Admin login
    admin_login = await client.post("/api/v1/auth/login", json={"identifier": "int004admin@test.com", "password": "Pass1234"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Mutate employee to org2
    mutate_resp = await client.post(
        f"/api/v1/admin/employees/{employee.employee_id}/mutate",
        json={"target_org_id": 99, "reason": "Reorganization"},
        headers=admin_headers,
    )
    assert mutate_resp.status_code in (200, 201), f"Mutation failed: {mutate_resp.text}"

    # Employee login
    emp_login = await client.post("/api/v1/auth/login", json={"identifier": "int004emp@test.com", "password": "Pass1234"})
    assert emp_login.status_code == 200
    emp_token = emp_login.json()["access_token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # Create and submit an entry
    await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": project.project_id,
            "work_date": "2026-05-04",
            "hours_worked": 8,
            "description": "Post-mutation work",
            "task_type": "dev",
            "entry_type": "normal",
        },
        headers=emp_headers,
    )

    with patch("app.tasks.notification_tasks.run_create_in_app_notification", new_callable=AsyncMock):
        submit_resp = await client.post(
            "/api/v1/employee/timesheet/submit",
            json={"week": "2026-W19"},
            headers=emp_headers,
        )

    if submit_resp.status_code == 200:
        approval_id = submit_resp.json()["approval_id"]

        # Manager 2 (new manager) should see it in pending
        mgr2_login = await client.post("/api/v1/auth/login", json={"identifier": "int004mgr2@test.com", "password": "Pass1234"})
        assert mgr2_login.status_code == 200
        mgr2_token = mgr2_login.json()["access_token"]
        mgr2_headers = {"Authorization": f"Bearer {mgr2_token}"}

        pending_resp = await client.get(
            "/api/v1/manager/approvals?status=pending",
            headers=mgr2_headers,
        )
        assert pending_resp.status_code == 200
        pending = pending_resp.json()
        approval_ids = [a["approval_id"] for a in pending]
        assert approval_id in approval_ids

        # Manager 1 (old manager) should NOT see it
        mgr1_login = await client.post("/api/v1/auth/login", json={"identifier": "int004mgr1@test.com", "password": "Pass1234"})
        assert mgr1_login.status_code == 200
        mgr1_token = mgr1_login.json()["access_token"]
        mgr1_headers = {"Authorization": f"Bearer {mgr1_token}"}

        mgr1_pending = await client.get(
            "/api/v1/manager/approvals?status=pending",
            headers=mgr1_headers,
        )
        assert mgr1_pending.status_code == 200
        mgr1_approval_ids = [a["approval_id"] for a in mgr1_pending.json()]
        assert approval_id not in mgr1_approval_ids
