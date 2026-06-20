"""Shared fixtures for unit tests — SQLite in-memory, no HTTP client needed."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock  # noqa: F401 — exported for test use

import bcrypt as _bcrypt
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.limiter import login_limiter, password_reset_limiter
from app.models.base import Base

# Register all models so SQLAlchemy metadata is complete
from app.models.employee import Employee  # noqa: F401
from app.models.auth import RefreshToken, LoginAttempt, PasswordResetToken  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.timesheet_entry import TimesheetEntry  # noqa: F401
from app.models.org_settings import OrgSettings  # noqa: F401
from app.models.approval import Approval  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.proxy_audit_log import ProxyAuditLog  # noqa: F401
from app.models.pending_employee import PendingEmployee  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_preference import NotificationPreference  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.invoice_audit_log import InvoiceAuditLog  # noqa: F401
from app.models.invoice_line_item import InvoiceLineItem  # noqa: F401
from app.models.export import Export  # noqa: F401
from app.models.organization_license import OrganizationLicense  # noqa: F401
from app.models.email_template import EmailTemplate  # noqa: F401
from app.models.employee_mutation_log import EmployeeMutationLog  # noqa: F401
from app.models.skill_rate import SkillRate  # noqa: F401
from app.models.project_team_member import ProjectTeamMember  # noqa: F401
from app.models.employee_skill import EmployeeSkill  # noqa: F401
from app.models.project_required_skill import ProjectRequiredSkill  # noqa: F401
from app.models.absence import Absence  # noqa: F401
from app.models.notification_log import NotificationLog  # noqa: F401
from app.models.module_license import ModuleLicense  # noqa: F401

# ---------------------------------------------------------------------------
# Engine (one per module — recreated each test session)
# ---------------------------------------------------------------------------

UNIT_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

unit_engine = create_async_engine(UNIT_TEST_DB_URL, echo=False)
UnitSessionLocal = async_sessionmaker(unit_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
def disable_route_rate_limiter(monkeypatch: pytest.MonkeyPatch):
    """Disable route-level pyrate limiter in unit tests.

    Unit tests should exercise business logic deterministically without
    cross-test throttling side effects.
    """

    async def _always_allow(*args, **kwargs):
        return True

    monkeypatch.setattr(login_limiter, "try_acquire_async", _always_allow)
    monkeypatch.setattr(password_reset_limiter, "try_acquire_async", _always_allow)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_unit_tables():
    async with unit_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with unit_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated async session for each test.

    Some services commit transactions during tests, so a simple rollback is not
    enough to keep state isolated. We clear all tables before and after each
    test to avoid cross-test UNIQUE collisions (e.g. employees.username).
    """
    async with UnitSessionLocal() as session:
        # Pre-clean in case a previous test committed data.
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f'DELETE FROM "{table.name}"'))
        await session.commit()

        yield session

        await session.rollback()
        # Post-clean to guarantee isolation for the next test.
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f'DELETE FROM "{table.name}"'))
        await session.commit()


# ---------------------------------------------------------------------------
# Low-level builder helpers
# ---------------------------------------------------------------------------

def _hash(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=4)).decode()


async def _make_org(db: AsyncSession, org_id: int = 1, manager_id: int | None = None) -> Organization:
    from sqlalchemy import select
    result = await db.execute(select(Organization).where(Organization.org_id == org_id))
    existing = result.scalar_one_or_none()
    if existing:
        if manager_id and existing.manager_id is None:
            existing.manager_id = manager_id
            await db.flush()
        return existing
    org = Organization(org_id=org_id, org_name=f"Test Org {org_id}", manager_id=manager_id)
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


async def _make_employee(
    db: AsyncSession,
    email: str = "user@test.com",
    password: str = "SecurePass123",
    role: str = "employee",
    status: str = "active",
    org_id: int = 1,
    manager_id: int | None = None,
    username: str | None = None,
    first_name: str = "Alice",
    last_name: str = "Martin",
    annual_leave_days: int = 25,
) -> Employee:
    await _make_org(db, org_id=org_id)
    emp = Employee(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password_hash=_hash(password),
        role=role,
        employment_status=status,
        org_id=org_id,
        manager_id=manager_id,
        username=username,
        must_change_password=False,
        annual_leave_days=annual_leave_days,
    )
    db.add(emp)
    await db.flush()
    await db.refresh(emp)
    if role == "manager":
        from sqlalchemy import update
        await db.execute(
            update(Organization)
            .where(Organization.org_id == org_id)
            .values(manager_id=emp.employee_id)
        )
        await db.flush()
    return emp


async def _make_client(db: AsyncSession, name: str = "Acme Corp") -> Client:
    c = Client(
        client_name=name,
        email=f"{name.lower().replace(' ', '')}@example.com",
        default_billing_rate=Decimal("100.00"),
        currency="EUR",
        client_status="active",
    )
    db.add(c)
    await db.flush()
    await db.refresh(c)
    return c


async def _make_project(
    db: AsyncSession,
    client_id: int,
    manager_id: int,
    name: str = "Project Alpha",
    status: str = "active",
    team_members: list[int] | None = None,
) -> Project:
    import random
    import string
    code = "P-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    p = Project(
        client_id=client_id,
        project_name=name,
        project_code=code,
        status=status,
        start_date=date(2025, 1, 1),
        billing_rate=Decimal("120.00"),
        manager_id=manager_id,
        team_members=team_members or [manager_id],
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return p


async def _make_entry(
    db: AsyncSession,
    employee_id: int,
    project_id: int,
    work_date: date,
    hours: float = 8.0,
    status: str = "draft",
    entry_type: str = "normal",
) -> TimesheetEntry:
    e = TimesheetEntry(
        employee_id=employee_id,
        project_id=project_id,
        work_date=work_date,
        hours_worked=Decimal(str(hours)),
        description="Test work",
        task_type="dev",
        entry_type=entry_type,
        billable_flag=True,
        status=status,
    )
    db.add(e)
    await db.flush()
    await db.refresh(e)
    return e


async def _make_approval(
    db: AsyncSession,
    employee_id: int,
    manager_id: int | None,
    week_start: date,
    status: str = "pending",
) -> Approval:
    a = Approval(
        employee_id=employee_id,
        manager_id=manager_id,
        week_start=week_start,
        status=status,
    )
    db.add(a)
    await db.flush()
    await db.refresh(a)
    return a


async def _make_org_settings(
    db: AsyncSession,
    org_id: int = 1,
    max_hours_per_day: float = 10.0,
    account_creation_lead_days: int = 7,
) -> OrgSettings:
    from sqlalchemy import select
    result = await db.execute(select(OrgSettings).where(OrgSettings.org_id == org_id))
    existing = result.scalar_one_or_none()
    if existing:
        existing.max_hours_per_day = Decimal(str(max_hours_per_day))
        existing.account_creation_lead_days = account_creation_lead_days
        await db.flush()
        return existing
    settings = OrgSettings(
        org_id=org_id,
        max_hours_per_day=Decimal(str(max_hours_per_day)),
        account_creation_lead_days=account_creation_lead_days,
    )
    db.add(settings)
    await db.flush()
    await db.refresh(settings)
    return settings


# ---------------------------------------------------------------------------
# Named fixtures used by tests
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def regular_employee(db: AsyncSession) -> Employee:
    return await _make_employee(
        db,
        email="employee@test.com",
        password="SecurePass123",
        role="employee",
        username="alice.martin",
    )


@pytest_asyncio.fixture
async def manager_employee(db: AsyncSession) -> Employee:
    emp = await _make_employee(
        db,
        email="manager@test.com",
        password="SecurePass123",
        role="manager",
        username="bob.manager",
        first_name="Bob",
        last_name="Manager",
    )
    return emp


@pytest_asyncio.fixture
async def admin_employee(db: AsyncSession) -> Employee:
    return await _make_employee(
        db,
        email="admin@test.com",
        password="SecurePass123",
        role="admin",
        username="carol.admin",
        first_name="Carol",
        last_name="Admin",
    )
