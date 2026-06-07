"""Integration tests — spec 13: multi-org-employee-model (task 12.1).

Covers:
  - Organizations CRUD (create valid/invalid manager, soft-delete)
  - Employee skills (add, duplicate, org mismatch, remove)
  - Employee mutation (org_id update, log creation, manager_id sync, blocked cases)
  - Employee suggestions (empty, absent exclusion, sort order)
  - Retrocompatibility (org_id=1 default)
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.employee_skill import EmployeeSkill
from app.models.employee_mutation_log import EmployeeMutationLog
from app.models.skill_rate import SkillRate
from app.models.absence import Absence
from app.models.project_required_skill import ProjectRequiredSkill
from tests.conftest import make_employee, make_client, make_project


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


async def make_organization(
    db: AsyncSession,
    org_name: str = "Test Org",
    manager_id: int | None = None,
) -> Organization:
    org = Organization(org_name=org_name, manager_id=manager_id)
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


async def make_skill_rate(
    db: AsyncSession,
    skill_name: str = "Python",
    org_id: int = 1,
    billing_rate: Decimal = Decimal("100.00"),
) -> SkillRate:
    sr = SkillRate(org_id=org_id, skill_name=skill_name, billing_rate=billing_rate)
    db.add(sr)
    await db.flush()
    await db.refresh(sr)
    return sr


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def admin(db: AsyncSession) -> Employee:
    uid = _uid()
    emp = await make_employee(db, email=f"admin-{uid}@example.com", role="admin")
    await db.commit()
    return emp


@pytest_asyncio.fixture
async def manager_emp(db: AsyncSession) -> Employee:
    uid = _uid()
    emp = await make_employee(db, email=f"mgr-{uid}@example.com", role="manager")
    await db.commit()
    return emp


# ===========================================================================
# ORGANISATIONS
# ===========================================================================

@pytest.mark.asyncio
async def test_create_organization_valid_manager(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """POST /admin/organizations with a valid manager → 201."""
    resp = await client.post(
        "/api/v1/admin/organizations",
        json={"org_name": f"Org-{_uid()}", "manager_id": manager_emp.employee_id},
        headers=_auth(admin),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["org_name"] is not None
    assert body["manager_id"] == manager_emp.employee_id
    assert "org_id" in body


@pytest.mark.asyncio
async def test_create_organization_invalid_manager(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """POST /admin/organizations with a non-manager employee → 422, code=invalid_manager."""
    uid = _uid()
    regular_emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    await db.commit()

    resp = await client.post(
        "/api/v1/admin/organizations",
        json={"org_name": f"Org-{uid}", "manager_id": regular_emp.employee_id},
        headers=_auth(admin),
    )
    assert resp.status_code == 422, resp.text
    detail = resp.json().get("detail", {})
    # detail may be a dict or a list of validation errors
    if isinstance(detail, dict):
        assert detail.get("code") == "invalid_manager"
    else:
        # FastAPI wraps HTTPException detail as-is; check raw text
        assert "invalid_manager" in resp.text


@pytest.mark.asyncio
async def test_soft_delete_organization_keeps_employees(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """DELETE /admin/organizations/{id} soft-deletes the org; employees keep their org_id."""
    uid = _uid()
    # Create org directly in DB
    org = await make_organization(db, org_name=f"Org-{uid}", manager_id=manager_emp.employee_id)
    await db.commit()

    # Create an employee in that org
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = org.org_id
    await db.flush()
    await db.commit()

    # Soft-delete the org via API
    resp = await client.delete(
        f"/api/v1/admin/organizations/{org.org_id}",
        headers=_auth(admin),
    )
    assert resp.status_code == 204, resp.text

    # Employee still exists with the same org_id
    result = await db.execute(select(Employee).where(Employee.employee_id == emp.employee_id))
    refreshed_emp = result.scalar_one_or_none()
    assert refreshed_emp is not None
    assert refreshed_emp.org_id == org.org_id

    # Org is soft-deleted (deleted_at is set)
    result = await db.execute(select(Organization).where(Organization.org_id == org.org_id))
    refreshed_org = result.scalar_one_or_none()
    assert refreshed_org is not None
    assert refreshed_org.deleted_at is not None


# ===========================================================================
# EMPLOYEE SKILLS
# ===========================================================================

@pytest.mark.asyncio
async def test_add_skill_to_employee(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """POST /admin/employees/{id}/skills → 201 with skill data."""
    uid = _uid()
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    skill = await make_skill_rate(db, skill_name=f"Skill-{uid}", org_id=1)
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/skills",
        json={"skill_rate_id": skill.id},
        headers=_auth(admin),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["employee_id"] == emp.employee_id
    assert body["skill_rate_id"] == skill.id


@pytest.mark.asyncio
async def test_add_duplicate_skill_returns_409(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """Adding the same skill twice → 409, code=skill_already_assigned."""
    uid = _uid()
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    skill = await make_skill_rate(db, skill_name=f"Skill-dup-{uid}", org_id=1)
    await db.commit()

    # First add — should succeed
    resp1 = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/skills",
        json={"skill_rate_id": skill.id},
        headers=_auth(admin),
    )
    assert resp1.status_code == 201, resp1.text

    # Second add — should conflict
    resp2 = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/skills",
        json={"skill_rate_id": skill.id},
        headers=_auth(admin),
    )
    assert resp2.status_code == 409, resp2.text
    detail = resp2.json().get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("code") == "skill_already_assigned"
    else:
        assert "skill_already_assigned" in resp2.text


@pytest.mark.asyncio
async def test_add_skill_wrong_org_returns_422(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """Adding a skill from a different org → 422, code=skill_org_mismatch."""
    uid = _uid()
    # Create a second org
    org2 = await make_organization(db, org_name=f"Org2-{uid}", manager_id=manager_emp.employee_id)
    # Employee is in org_id=1, skill belongs to org2
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    skill_other_org = await make_skill_rate(db, skill_name=f"Skill-other-{uid}", org_id=org2.org_id)
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/skills",
        json={"skill_rate_id": skill_other_org.id},
        headers=_auth(admin),
    )
    assert resp.status_code == 422, resp.text
    detail = resp.json().get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("code") == "skill_org_mismatch"
    else:
        assert "skill_org_mismatch" in resp.text


@pytest.mark.asyncio
async def test_remove_skill_does_not_affect_team(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """DELETE /admin/employees/{id}/skills/{skill_rate_id} → 204; employee still exists."""
    uid = _uid()
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    skill = await make_skill_rate(db, skill_name=f"Skill-rm-{uid}", org_id=1)
    # Assign skill directly in DB
    es = EmployeeSkill(employee_id=emp.employee_id, skill_rate_id=skill.id)
    db.add(es)
    await db.commit()

    resp = await client.delete(
        f"/api/v1/admin/employees/{emp.employee_id}/skills/{skill.id}",
        headers=_auth(admin),
    )
    assert resp.status_code == 204, resp.text

    # Skill row is gone
    result = await db.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == emp.employee_id,
            EmployeeSkill.skill_rate_id == skill.id,
        )
    )
    assert result.scalar_one_or_none() is None

    # Employee still exists
    result = await db.execute(select(Employee).where(Employee.employee_id == emp.employee_id))
    assert result.scalar_one_or_none() is not None


# ===========================================================================
# MUTATION
# ===========================================================================

@pytest.mark.asyncio
async def test_mutate_employee_updates_org_id(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """POST /admin/employees/{id}/mutate → employee.org_id updated in DB."""
    uid = _uid()
    org2 = await make_organization(db, org_name=f"Org2-{uid}", manager_id=manager_emp.employee_id)
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/mutate",
        json={"target_org_id": org2.org_id, "reason": "Reorganisation"},
        headers=_auth(admin),
    )
    assert resp.status_code == 200, resp.text

    # Verify org_id updated in DB — re-query by known PK (don't rely on expired ORM state)
    emp_id = emp.employee_id
    db.expire(emp)
    result = await db.execute(select(Employee).where(Employee.employee_id == emp_id))
    refreshed = result.scalar_one()
    assert refreshed.org_id == org2.org_id


@pytest.mark.asyncio
async def test_mutate_employee_creates_log(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """POST /admin/employees/{id}/mutate → log entry created in employee_mutation_logs."""
    uid = _uid()
    org2 = await make_organization(db, org_name=f"Org2-{uid}", manager_id=manager_emp.employee_id)
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    await db.commit()

    from_org_id = emp.org_id

    resp = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/mutate",
        json={"target_org_id": org2.org_id, "reason": "Test log"},
        headers=_auth(admin),
    )
    assert resp.status_code == 200, resp.text

    # Verify log exists
    result = await db.execute(
        select(EmployeeMutationLog).where(
            EmployeeMutationLog.employee_id == emp.employee_id,
            EmployeeMutationLog.to_org_id == org2.org_id,
        )
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.from_org_id == from_org_id
    assert log.to_org_id == org2.org_id
    assert log.reason == "Test log"


@pytest.mark.asyncio
async def test_mutate_employee_syncs_manager_id(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """POST /admin/employees/{id}/mutate → employee.manager_id synced to target org's manager."""
    uid = _uid()
    org2 = await make_organization(db, org_name=f"Org2-{uid}", manager_id=manager_emp.employee_id)
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/mutate",
        json={"target_org_id": org2.org_id},
        headers=_auth(admin),
    )
    assert resp.status_code == 200, resp.text

    # Verify manager_id synced — re-query by known PK
    emp_id = emp.employee_id
    mgr_id = manager_emp.employee_id
    db.expire(emp)
    result = await db.execute(select(Employee).where(Employee.employee_id == emp_id))
    refreshed = result.scalar_one()
    assert refreshed.manager_id == mgr_id, \
        f"Expected manager_id={mgr_id}, got {refreshed.manager_id}"


@pytest.mark.asyncio
async def test_mutate_blocked_employee_is_org_manager(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """Mutating an employee who is manager of an org → 422, code=employee_is_org_manager."""
    uid = _uid()
    # The employee IS the manager of an org
    mgr = await make_employee(db, email=f"mgr-{uid}@example.com", role="manager")
    org = await make_organization(db, org_name=f"Org-{uid}", manager_id=mgr.employee_id)

    # Create a target org managed by admin
    target_org = await make_organization(
        db, org_name=f"Target-{uid}", manager_id=admin.employee_id
    )
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/employees/{mgr.employee_id}/mutate",
        json={"target_org_id": target_org.org_id},
        headers=_auth(admin),
    )
    assert resp.status_code == 422, resp.text
    detail = resp.json().get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("code") == "employee_is_org_manager"
    else:
        assert "employee_is_org_manager" in resp.text


@pytest.mark.asyncio
async def test_mutate_blocked_invalid_target_org(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """Mutating to a non-existent org → 422, code=invalid_target_organization."""
    uid = _uid()
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee")
    emp.org_id = 1
    await db.commit()

    resp = await client.post(
        f"/api/v1/admin/employees/{emp.employee_id}/mutate",
        json={"target_org_id": 999999},
        headers=_auth(admin),
    )
    assert resp.status_code == 422, resp.text
    detail = resp.json().get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("code") == "invalid_target_organization"
    else:
        assert "invalid_target_organization" in resp.text


# ===========================================================================
# SUGGESTIONS
# ===========================================================================

@pytest.mark.asyncio
async def test_suggest_employees_empty_if_no_skills(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """GET /admin/projects/{id}/suggested-employees → [] when no employee has required skills."""
    uid = _uid()
    cli = await make_client(db, name=f"Client-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager_emp.employee_id)

    # Add a required skill to the project
    skill = await make_skill_rate(db, skill_name=f"Rare-{uid}", org_id=1)
    prs = ProjectRequiredSkill(project_id=proj.project_id, skill_rate_id=skill.id, quantity=1)
    db.add(prs)
    await db.commit()

    # No employee has this skill → suggestions should be empty
    resp = await client.get(
        f"/api/v1/admin/projects/{proj.project_id}/suggested-employees",
        headers=_auth(admin),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


@pytest.mark.asyncio
async def test_suggest_employees_excludes_absent(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """Employees absent for the entire project period are excluded from suggestions."""
    uid = _uid()
    cli = await make_client(db, name=f"Client-{uid}")

    # Project with fixed dates
    from decimal import Decimal as D
    import random, string
    code = "P-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    from app.models.project import Project
    proj = Project(
        client_id=cli.client_id,
        project_name=f"Proj-{uid}",
        project_code=code,
        status="active",
        start_date=date(2025, 6, 1),
        end_date=date(2025, 6, 30),
        billing_rate=D("100.00"),
        manager_id=manager_emp.employee_id,
        team_members=[manager_emp.employee_id],
    )
    db.add(proj)
    await db.flush()
    await db.refresh(proj)

    # Skill and employee
    skill = await make_skill_rate(db, skill_name=f"Skill-abs-{uid}", org_id=1)
    emp = await make_employee(db, email=f"emp-abs-{uid}@example.com", role="employee")
    emp.org_id = 1

    # Assign skill to employee
    es = EmployeeSkill(employee_id=emp.employee_id, skill_rate_id=skill.id)
    db.add(es)

    # Required skill on project
    prs = ProjectRequiredSkill(project_id=proj.project_id, skill_rate_id=skill.id, quantity=1)
    db.add(prs)

    # Absence covering the entire project period
    absence = Absence(
        employee_id=emp.employee_id,
        absence_type="cp",
        start_date=date(2025, 5, 31),  # starts before project
        end_date=date(2025, 7, 1),     # ends after project
        status="approved",
    )
    db.add(absence)
    await db.commit()

    resp = await client.get(
        f"/api/v1/admin/projects/{proj.project_id}/suggested-employees",
        headers=_auth(admin),
    )
    assert resp.status_code == 200, resp.text
    suggestions = resp.json()
    # The absent employee must not appear
    absent_ids = [s["employee_id"] for s in suggestions]
    assert emp.employee_id not in absent_ids


@pytest.mark.asyncio
async def test_suggest_employees_sorted_by_count(
    client: AsyncClient, db: AsyncSession, admin: Employee, manager_emp: Employee
):
    """Suggestions are sorted by matching_skill_count descending."""
    uid = _uid()
    cli = await make_client(db, name=f"Client-{uid}")

    from decimal import Decimal as D
    import random, string
    code = "P-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    from app.models.project import Project
    proj = Project(
        client_id=cli.client_id,
        project_name=f"Proj-sort-{uid}",
        project_code=code,
        status="active",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 31),
        billing_rate=D("100.00"),
        manager_id=manager_emp.employee_id,
        team_members=[manager_emp.employee_id],
    )
    db.add(proj)
    await db.flush()
    await db.refresh(proj)

    # Two skills
    skill_a = await make_skill_rate(db, skill_name=f"SkillA-{uid}", org_id=1)
    skill_b = await make_skill_rate(db, skill_name=f"SkillB-{uid}", org_id=1)

    # emp_one has both skills
    emp_one = await make_employee(db, email=f"emp-one-{uid}@example.com", role="employee")
    emp_one.org_id = 1
    # emp_two has only one skill
    emp_two = await make_employee(db, email=f"emp-two-{uid}@example.com", role="employee")
    emp_two.org_id = 1

    db.add(EmployeeSkill(employee_id=emp_one.employee_id, skill_rate_id=skill_a.id))
    db.add(EmployeeSkill(employee_id=emp_one.employee_id, skill_rate_id=skill_b.id))
    db.add(EmployeeSkill(employee_id=emp_two.employee_id, skill_rate_id=skill_a.id))

    # Both skills required
    db.add(ProjectRequiredSkill(project_id=proj.project_id, skill_rate_id=skill_a.id, quantity=1))
    db.add(ProjectRequiredSkill(project_id=proj.project_id, skill_rate_id=skill_b.id, quantity=1))
    await db.commit()

    resp = await client.get(
        f"/api/v1/admin/projects/{proj.project_id}/suggested-employees",
        headers=_auth(admin),
    )
    assert resp.status_code == 200, resp.text
    suggestions = resp.json()

    # Filter to only our test employees
    our_ids = {emp_one.employee_id, emp_two.employee_id}
    our_suggestions = [s for s in suggestions if s["employee_id"] in our_ids]

    assert len(our_suggestions) == 2
    # emp_one (2 skills) must come before emp_two (1 skill)
    counts = [s["matching_skill_count"] for s in our_suggestions]
    assert counts == sorted(counts, reverse=True)
    assert our_suggestions[0]["employee_id"] == emp_one.employee_id


# ===========================================================================
# RETROCOMPATIBILITY
# ===========================================================================

@pytest.mark.asyncio
async def test_existing_employees_have_org_id_1(db: AsyncSession):
    """Employees created without explicit org_id default to org_id=1 (retrocompatibility)."""
    uid = _uid()
    emp = await make_employee(db, email=f"retro-{uid}@example.com", role="employee")
    await db.commit()

    result = await db.execute(select(Employee).where(Employee.employee_id == emp.employee_id))
    refreshed = result.scalar_one()
    assert refreshed.org_id == 1
