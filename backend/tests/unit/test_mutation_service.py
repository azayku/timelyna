"""Unit tests for MutationService — TEST-MUT-001 through TEST-MUT-003."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.employee_mutation_log import EmployeeMutationLog
from app.models.organization import Organization
from app.services.mutation_service import MutationService

from tests.unit.conftest import _make_employee, _make_org


# ---------------------------------------------------------------------------
# TEST-MUT-001 — mutate employee to new org success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mutate_employee_to_new_org_success(db: AsyncSession):
    # Org 1 with manager_a
    org1 = await _make_org(db, org_id=1)
    manager_a = await _make_employee(
        db, email="mut001mgra@test.com", role="manager", org_id=1
    )
    employee = await _make_employee(
        db, email="mut001emp@test.com", role="employee", org_id=1, manager_id=manager_a.employee_id
    )

    # Org 2 with manager_b (id=10 as per spec scenario)
    org2 = await _make_org(db, org_id=2)
    manager_b = await _make_employee(
        db, email="mut001mgrb@test.com", role="manager", org_id=2
    )
    # Update org2 manager_id to manager_b
    from sqlalchemy import update
    await db.execute(
        update(Organization).where(Organization.org_id == 2).values(manager_id=manager_b.employee_id)
    )
    await db.commit()

    admin = await _make_employee(db, email="mut001admin@test.com", role="admin")
    await db.commit()

    with patch("app.tasks.email_tasks.task_send_mutation_notification") as mock_task:
        mock_task.delay = MagicMock()
        service = MutationService(db)
        log = await service.mutate_employee(
            employee_id=employee.employee_id,
            target_org_id=2,
            mutated_by=admin.employee_id,
            reason="Reorganization",
        )

    assert log.employee_id == employee.employee_id
    assert log.from_org_id == 1
    assert log.to_org_id == 2

    # Employee should now be in org 2 with manager_b
    res = await db.execute(
        select(Employee).where(Employee.employee_id == employee.employee_id)
    )
    updated_emp = res.scalar_one()
    assert updated_emp.org_id == 2
    assert updated_emp.manager_id == manager_b.employee_id

    # Mutation log should exist
    log_res = await db.execute(
        select(EmployeeMutationLog).where(EmployeeMutationLog.id == log.id)
    )
    saved_log = log_res.scalar_one_or_none()
    assert saved_log is not None


# ---------------------------------------------------------------------------
# TEST-MUT-002 — mutate org manager raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mutate_org_manager_raises_422(db: AsyncSession):
    org1 = await _make_org(db, org_id=40)
    manager = await _make_employee(
        db, email="mut002mgr@test.com", role="manager", org_id=40
    )
    org2 = await _make_org(db, org_id=41)
    await db.commit()

    admin = await _make_employee(db, email="mut002admin@test.com", role="admin")
    await db.commit()

    service = MutationService(db)
    # The manager is manager of org 40 — cannot be mutated
    with pytest.raises(HTTPException) as exc_info:
        await service.mutate_employee(
            employee_id=manager.employee_id,
            target_org_id=41,
            mutated_by=admin.employee_id,
        )

    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    if isinstance(detail, dict):
        assert detail.get("code") == "employee_is_org_manager"
    else:
        assert "manager" in str(detail).lower()


# ---------------------------------------------------------------------------
# TEST-MUT-003 — mutate to inactive (soft-deleted) org raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mutate_to_inactive_org_raises_422(db: AsyncSession):
    org1 = await _make_org(db, org_id=50)
    employee = await _make_employee(
        db, email="mut003emp@test.com", role="employee", org_id=50
    )

    # Create a soft-deleted org
    deleted_org = Organization(
        org_id=51,
        org_name="Deleted Org",
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(deleted_org)
    await db.commit()

    admin = await _make_employee(db, email="mut003admin@test.com", role="admin")
    await db.commit()

    service = MutationService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.mutate_employee(
            employee_id=employee.employee_id,
            target_org_id=51,
            mutated_by=admin.employee_id,
        )

    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    if isinstance(detail, dict):
        assert detail.get("code") == "invalid_target_organization"
    else:
        assert "organization" in str(detail).lower()
