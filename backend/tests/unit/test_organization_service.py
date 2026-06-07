"""Unit tests for OrganizationService — TEST-ORG-001 through TEST-ORG-004."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.organization import Organization
from app.services.organization_service import OrganizationService

from tests.unit.conftest import _make_employee, _make_org


# ---------------------------------------------------------------------------
# TEST-ORG-001 — create organization with valid manager
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_organization_with_valid_manager(db: AsyncSession):
    manager = await _make_employee(
        db,
        email="org001mgr@test.com",
        role="manager",
        first_name="Valid",
        last_name="Manager",
    )
    await db.commit()

    service = OrganizationService(db)
    org = await service.create_organization(
        org_name="Org Alpha",
        manager_id=manager.employee_id,
    )

    assert org.org_name == "Org Alpha"
    assert org.manager_id == manager.employee_id
    assert org.org_id is not None

    # Verify in DB
    res = await db.execute(select(Organization).where(Organization.org_id == org.org_id))
    db_org = res.scalar_one_or_none()
    assert db_org is not None
    assert db_org.manager_id == manager.employee_id


# ---------------------------------------------------------------------------
# TEST-ORG-002 — create organization with employee role raises 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_organization_with_employee_role_raises_422(db: AsyncSession):
    non_manager = await _make_employee(
        db,
        email="org002emp@test.com",
        role="employee",
    )
    await db.commit()

    service = OrganizationService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_organization(
            org_name="Invalid Org",
            manager_id=non_manager.employee_id,
        )

    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    # Should contain "invalid_manager" code
    if isinstance(detail, dict):
        assert detail.get("code") == "invalid_manager"
    else:
        assert "invalid_manager" in str(detail).lower() or "manager" in str(detail).lower()


# ---------------------------------------------------------------------------
# TEST-ORG-003 — list organizations includes employee count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_organizations_includes_employee_count(db: AsyncSession):
    # Org A with 5 active employees (use different org_ids to avoid conflicts)
    org_a = await _make_org(db, org_id=30)
    manager_a = await _make_employee(db, email="org003mgra@test.com", role="manager", org_id=30)

    for i in range(4):  # 4 more employees (+ manager = 5 total)
        await _make_employee(db, email=f"org003empa{i}@test.com", org_id=30)

    # Org B with 3 active employees
    org_b = await _make_org(db, org_id=31)
    manager_b = await _make_employee(db, email="org003mgrb@test.com", role="manager", org_id=31)
    for i in range(2):
        await _make_employee(db, email=f"org003empb{i}@test.com", org_id=31)

    await db.commit()

    service = OrganizationService(db)
    orgs = await service.list_organizations()

    # Find org A and org B in results
    org_a_data = next((o for o in orgs if o["org_id"] == org_a.org_id), None)
    org_b_data = next((o for o in orgs if o["org_id"] == org_b.org_id), None)

    assert org_a_data is not None
    assert org_b_data is not None
    assert org_a_data["employee_count"] == 5
    assert org_b_data["employee_count"] == 3


# ---------------------------------------------------------------------------
# TEST-ORG-004 — soft delete organization marks deleted_at
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_organization_marks_deleted_at(db: AsyncSession):
    manager = await _make_employee(db, email="org004mgr@test.com", role="manager")

    service = OrganizationService(db)
    org = await service.create_organization(
        org_name="ToDelete Org",
        manager_id=manager.employee_id,
    )

    # Verify it appears in listing before deletion
    orgs_before = await service.list_organizations()
    assert any(o["org_id"] == org.org_id for o in orgs_before)

    await service.soft_delete(org.org_id)

    # deleted_at should be set
    res = await db.execute(select(Organization).where(Organization.org_id == org.org_id))
    deleted_org = res.scalar_one()
    assert deleted_org.deleted_at is not None

    # Should not appear in list_organizations() anymore
    orgs_after = await service.list_organizations()
    assert not any(o["org_id"] == org.org_id for o in orgs_after)
