"""Property-based tests — spec 13: multi-org-employee-model (task 12.2).

Each test is annotated with the property it validates:
  # Feature: multi-org-employee-model, Property N: <text>

Uses Hypothesis with settings(max_examples=50) for reasonable CI speed.
All tests are self-contained: they create their own data and do not rely on
shared state between examples.

Design notes:
- Hypothesis @given tests are synchronous; async DB work is wrapped with
  asyncio.run() using a dedicated event loop per call to avoid conflicts
  with pytest-asyncio's session-scoped loop.
- The Celery mutation notification task is patched to a no-op so tests
  don't attempt real network/DB connections outside the test session.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import TestSessionLocal, make_employee
from app.models.employee import Employee
from app.models.employee_skill import EmployeeSkill
from app.models.employee_mutation_log import EmployeeMutationLog
from app.models.organization import Organization
from app.models.skill_rate import SkillRate
from app.models.absence import Absence
from app.models.project import Project
from app.models.project_required_skill import ProjectRequiredSkill
from app.repositories.employee_skill_repository import EmployeeSkillRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.mutation_service import MutationService
from app.services.employee_suggestion_service import EmployeeSuggestionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _run_async(coro):
    """Run an async coroutine in a fresh event loop (safe for Hypothesis sync tests)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _make_org(db: AsyncSession, manager_id: int, name: str | None = None) -> Organization:
    org = Organization(org_name=name or f"Org-{_uid()}", manager_id=manager_id)
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


async def _make_skill(db: AsyncSession, org_id: int, name: str | None = None) -> SkillRate:
    sr = SkillRate(
        org_id=org_id,
        skill_name=name or f"Skill-{_uid()}",
        billing_rate=Decimal("80.00"),
    )
    db.add(sr)
    await db.flush()
    await db.refresh(sr)
    return sr


async def _make_client(db: AsyncSession, uid: str):
    from app.models.client import Client
    cli = Client(
        client_name=f"Cli-{uid}",
        email=f"cli-{uid}@example.com",
        default_billing_rate=Decimal("100.00"),
        currency="EUR",
        client_status="active",
    )
    db.add(cli)
    await db.flush()
    await db.refresh(cli)
    return cli


async def _make_project(
    db: AsyncSession,
    client_id: int,
    manager_id: int,
    uid: str,
    start_date: date,
    end_date: date,
) -> Project:
    # Use uid (already a UUID hex) as the project code suffix — guaranteed unique per call
    code = f"P-{uid[:8].upper()}"
    proj = Project(
        client_id=client_id,
        project_name=f"Proj-{uid}",
        project_code=code,
        status="active",
        start_date=start_date,
        end_date=end_date,
        billing_rate=Decimal("100.00"),
        manager_id=manager_id,
        team_members=[manager_id],
    )
    db.add(proj)
    await db.flush()
    await db.refresh(proj)
    return proj


# ---------------------------------------------------------------------------
# Mock for Celery task — prevents real DB/network calls during mutation
# ---------------------------------------------------------------------------

_MOCK_CELERY_TASK = MagicMock()
_MOCK_CELERY_TASK.delay = MagicMock()


# ===========================================================================
# P2 — Unicité (employee_id, skill_rate_id)
# ===========================================================================

# Feature: multi-org-employee-model, Property 2: Unicité (employee_id, skill_rate_id)
# For any pair (employee_id, skill_rate_id), only one row can exist in employee_skills.
# A duplicate insertion must raise an error.

@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_p2_unique_employee_skill_constraint(dummy: int):
    """Inserting the same (employee_id, skill_rate_id) twice raises an error."""

    async def _inner():
        async with TestSessionLocal() as db:
            uid = _uid()
            emp = await make_employee(db, email=f"p2-{uid}@example.com", role="employee")
            emp.org_id = 1
            skill = await _make_skill(db, org_id=1)
            await db.flush()

            repo = EmployeeSkillRepository(db)
            # First insertion — must succeed
            await repo.add(employee_id=emp.employee_id, skill_rate_id=skill.id)

            # Second insertion — must raise (HTTPException 409 or IntegrityError)
            from fastapi import HTTPException
            from sqlalchemy.exc import IntegrityError
            raised = False
            try:
                await repo.add(employee_id=emp.employee_id, skill_rate_id=skill.id)
            except (HTTPException, IntegrityError):
                raised = True
            finally:
                await db.rollback()

            assert raised, "Duplicate (employee_id, skill_rate_id) should raise an error"

    _run_async(_inner())


# ===========================================================================
# P4 — Mutation round-trip: org_id + log + manager_id synchronisés
# ===========================================================================

# Feature: multi-org-employee-model, Property 4: Mutation round-trip
# For any employee mutated from org A to org B:
#   - employees.org_id == B after mutation
#   - a log entry exists with from_org_id=A, to_org_id=B
#   - employees.manager_id == organizations.manager_id of org B

@given(st.text(
    min_size=1,
    max_size=20,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
))
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_p4_mutation_round_trip(reason_suffix: str):
    """Mutation updates org_id, creates log, and syncs manager_id."""

    async def _inner():
        async with TestSessionLocal() as db:
            uid = _uid()
            admin = await make_employee(db, email=f"p4-admin-{uid}@example.com", role="admin")
            mgr = await make_employee(db, email=f"p4-mgr-{uid}@example.com", role="manager")
            emp = await make_employee(db, email=f"p4-emp-{uid}@example.com", role="employee")
            emp.org_id = 1
            await db.flush()

            target_org = await _make_org(db, manager_id=mgr.employee_id)
            from_org_id = emp.org_id
            emp_id = emp.employee_id
            target_org_id = target_org.org_id
            mgr_id = mgr.employee_id
            admin_id = admin.employee_id
            await db.commit()

            # Patch the Celery task at its source so the mutation service's
            # dynamic import resolves to the mock (avoids real broker/DB calls)
            with patch(
                "app.tasks.email_tasks.task_send_mutation_notification",
                _MOCK_CELERY_TASK,
            ):
                svc = MutationService(db)
                await svc.mutate_employee(
                    employee_id=emp_id,
                    target_org_id=target_org_id,
                    mutated_by=admin_id,
                    reason=f"reason-{reason_suffix}",
                )

            # Verify org_id updated
            result = await db.execute(select(Employee).where(Employee.employee_id == emp_id))
            refreshed_emp = result.scalar_one()
            assert refreshed_emp.org_id == target_org_id, \
                f"Expected org_id={target_org_id}, got {refreshed_emp.org_id}"

            # Verify log created
            log_result = await db.execute(
                select(EmployeeMutationLog).where(
                    EmployeeMutationLog.employee_id == emp_id,
                    EmployeeMutationLog.to_org_id == target_org_id,
                )
            )
            db_log = log_result.scalar_one_or_none()
            assert db_log is not None, "Mutation log must be created"
            assert db_log.from_org_id == from_org_id
            assert db_log.to_org_id == target_org_id

            # Verify manager_id synced
            assert refreshed_emp.manager_id == mgr_id, \
                f"Expected manager_id={mgr_id}, got {refreshed_emp.manager_id}"

    _run_async(_inner())


# ===========================================================================
# P6 — Suggestions: tous les résultats ont ≥1 compétence requise
# ===========================================================================

# Feature: multi-org-employee-model, Property 6: Suggestions — compétences correspondantes
# For any project with required skills, every suggested employee must have
# at least one of the required skills in employee_skills.

@given(st.integers(min_value=1, max_value=3))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_p6_suggestions_have_required_skill(num_skills: int):
    """All suggested employees have at least one required skill."""

    async def _inner():
        async with TestSessionLocal() as db:
            uid = _uid()
            mgr = await make_employee(db, email=f"p6-mgr-{uid}@example.com", role="manager")
            cli = await _make_client(db, uid)
            proj = await _make_project(
                db, cli.client_id, mgr.employee_id, uid,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 31),
            )

            # Create required skills
            skills = []
            for i in range(num_skills):
                s = await _make_skill(db, org_id=1, name=f"P6Skill{i}-{uid}")
                skills.append(s)
                db.add(ProjectRequiredSkill(
                    project_id=proj.project_id, skill_rate_id=s.id, quantity=1
                ))

            # emp_with gets the first required skill
            emp_with = await make_employee(db, email=f"p6-with-{uid}@example.com", role="employee")
            emp_with.org_id = 1
            # emp_without gets only an unrelated skill
            emp_without = await make_employee(db, email=f"p6-without-{uid}@example.com", role="employee")
            emp_without.org_id = 1
            await db.flush()

            db.add(EmployeeSkill(employee_id=emp_with.employee_id, skill_rate_id=skills[0].id))
            unrelated = await _make_skill(db, org_id=1, name=f"Unrelated-{uid}")
            db.add(EmployeeSkill(employee_id=emp_without.employee_id, skill_rate_id=unrelated.id))
            await db.commit()

            svc = EmployeeSuggestionService(db)
            suggestions = await svc.suggest_employees(proj.project_id)

            # Every suggestion must have at least one matching skill
            for suggestion in suggestions:
                assert len(suggestion["matching_skills"]) >= 1, \
                    f"Employee {suggestion['employee_id']} has no matching skills"

            # emp_without must NOT appear
            suggested_ids = {s["employee_id"] for s in suggestions}
            assert emp_without.employee_id not in suggested_ids, \
                "Employee without required skills must not be suggested"

    _run_async(_inner())


# ===========================================================================
# P7 — Suggestions: employés absents sur toute la période exclus
# ===========================================================================

# Feature: multi-org-employee-model, Property 7: Suggestions — disponibilité (absence)
# For any project with a [start_date, end_date] period, no suggested employee
# should have an approved absence covering the entire period.

@given(
    st.integers(min_value=1, max_value=20),   # project start day
    st.integers(min_value=1, max_value=8),    # project duration in days
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_p7_absent_employees_excluded(start_day: int, duration: int):
    """Employees with an approved absence covering the full project period are excluded."""

    async def _inner():
        async with TestSessionLocal() as db:
            uid = _uid()
            mgr = await make_employee(db, email=f"p7-mgr-{uid}@example.com", role="manager")
            cli = await _make_client(db, uid)

            proj_start = date(2025, 9, start_day)
            proj_end = proj_start + timedelta(days=duration)

            proj = await _make_project(
                db, cli.client_id, mgr.employee_id, uid,
                start_date=proj_start,
                end_date=proj_end,
            )

            skill = await _make_skill(db, org_id=1, name=f"P7Skill-{uid}")
            db.add(ProjectRequiredSkill(
                project_id=proj.project_id, skill_rate_id=skill.id, quantity=1
            ))

            # Absent employee: has the skill but is absent for the whole period
            emp_absent = await make_employee(
                db, email=f"p7-absent-{uid}@example.com", role="employee"
            )
            emp_absent.org_id = 1
            await db.flush()
            db.add(EmployeeSkill(employee_id=emp_absent.employee_id, skill_rate_id=skill.id))

            # Absence covers the entire project period (starts before, ends after)
            absence = Absence(
                employee_id=emp_absent.employee_id,
                absence_type="cp",
                start_date=proj_start - timedelta(days=1),
                end_date=proj_end + timedelta(days=1),
                status="approved",
            )
            db.add(absence)
            await db.commit()

            svc = EmployeeSuggestionService(db)
            suggestions = await svc.suggest_employees(proj.project_id)

            suggested_ids = {s["employee_id"] for s in suggestions}
            assert emp_absent.employee_id not in suggested_ids, \
                f"Absent employee {emp_absent.employee_id} must not appear in suggestions"

    _run_async(_inner())


# ===========================================================================
# P8 — Suggestions: tri décroissant par matching_skill_count
# ===========================================================================

# Feature: multi-org-employee-model, Property 8: Suggestions — tri décroissant
# For any list of suggestions returned, matching_skill_count of each element
# must be >= that of the next element (descending order).

@given(st.integers(min_value=2, max_value=4))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_p8_suggestions_sorted_descending(num_employees: int):
    """Suggestions are sorted by matching_skill_count in descending order."""

    async def _inner():
        async with TestSessionLocal() as db:
            uid = _uid()
            mgr = await make_employee(db, email=f"p8-mgr-{uid}@example.com", role="manager")
            cli = await _make_client(db, uid)
            proj = await _make_project(
                db, cli.client_id, mgr.employee_id, uid,
                start_date=date(2025, 10, 1),
                end_date=date(2025, 10, 31),
            )

            # Create num_employees required skills
            skills = []
            for i in range(num_employees):
                s = await _make_skill(db, org_id=1, name=f"P8Skill{i}-{uid}")
                skills.append(s)
                db.add(ProjectRequiredSkill(
                    project_id=proj.project_id, skill_rate_id=s.id, quantity=1
                ))

            # Employee i gets skills[0..i] → i+1 matching skills
            for i in range(num_employees):
                emp = await make_employee(
                    db, email=f"p8-emp{i}-{uid}@example.com", role="employee"
                )
                emp.org_id = 1
                await db.flush()
                for j in range(i + 1):
                    db.add(EmployeeSkill(
                        employee_id=emp.employee_id, skill_rate_id=skills[j].id
                    ))

            await db.commit()

            svc = EmployeeSuggestionService(db)
            suggestions = await svc.suggest_employees(proj.project_id)

            counts = [s["matching_skill_count"] for s in suggestions]
            assert counts == sorted(counts, reverse=True), \
                f"Suggestions not sorted descending: {counts}"

    _run_async(_inner())


# ===========================================================================
# P10 — Soft-delete org: employés toujours présents
# ===========================================================================

# Feature: multi-org-employee-model, Property 10: Soft-delete organisation — employés conservés
# For any soft-deleted organization, employees attached to it must still exist
# in the employees table with their org_id unchanged.

@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_p10_soft_delete_org_keeps_employees(num_employees: int):
    """Soft-deleting an org does not delete or modify its employees."""

    async def _inner():
        async with TestSessionLocal() as db:
            uid = _uid()
            mgr = await make_employee(db, email=f"p10-mgr-{uid}@example.com", role="manager")
            org = await _make_org(db, manager_id=mgr.employee_id, name=f"P10Org-{uid}")
            await db.flush()

            # Create employees in this org
            emp_ids = []
            for i in range(num_employees):
                emp = await make_employee(
                    db, email=f"p10-emp{i}-{uid}@example.com", role="employee"
                )
                emp.org_id = org.org_id
                await db.flush()
                emp_ids.append(emp.employee_id)

            org_id = org.org_id
            await db.commit()

            # Soft-delete the org
            org_repo = OrganizationRepository(db)
            await org_repo.soft_delete(org_id)
            await db.commit()

            # Verify org is soft-deleted
            result = await db.execute(
                select(Organization).where(Organization.org_id == org_id)
            )
            refreshed_org = result.scalar_one_or_none()
            assert refreshed_org is not None
            assert refreshed_org.deleted_at is not None, "Org must have deleted_at set"

            # Verify all employees still exist with the same org_id
            for eid in emp_ids:
                result = await db.execute(
                    select(Employee).where(Employee.employee_id == eid)
                )
                emp = result.scalar_one_or_none()
                assert emp is not None, f"Employee {eid} must still exist after org soft-delete"
                assert emp.org_id == org_id, \
                    f"Employee {eid} org_id changed: expected {org_id}, got {emp.org_id}"

    _run_async(_inner())
