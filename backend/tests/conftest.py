"""Shared pytest fixtures for all backend tests."""
from __future__ import annotations

from datetime import date
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.limiter import login_limiter, password_reset_limiter
from app.main import app
from app.models.base import Base
from app.models.employee import Employee  # noqa: F401 — register models
from app.models.auth import RefreshToken, LoginAttempt, PasswordResetToken  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.timesheet_entry import TimesheetEntry  # noqa: F401
from app.models.org_settings import OrgSettings  # noqa: F401
from app.models.approval import Approval  # noqa: F401
from app.models.export import Export  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.organization_license import OrganizationLicense  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_preference import NotificationPreference  # noqa: F401
from app.models.skill_rate import SkillRate  # noqa: F401
from app.models.project_team_member import ProjectTeamMember  # noqa: F401
from app.models.email_template import EmailTemplate  # noqa: F401
from app.models.invoice_audit_log import InvoiceAuditLog  # noqa: F401
from app.models.proxy_audit_log import ProxyAuditLog  # noqa: F401
from app.models.pending_employee import PendingEmployee  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.employee_skill import EmployeeSkill  # noqa: F401
from app.models.project_required_skill import ProjectRequiredSkill  # noqa: F401
from app.models.employee_mutation_log import EmployeeMutationLog  # noqa: F401

# Use SQLite in-memory for tests (no Postgres needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
def disable_route_rate_limiter(monkeypatch: pytest.MonkeyPatch):
    """Disable route-level pyrate limiter in tests.

    Authentication lockout tests rely on DB-backed login attempts, not this
    per-route limiter. Disabling it avoids cross-test 429 cascades.
    """

    async def _always_allow(*args, **kwargs):
        return True

    monkeypatch.setattr(login_limiter, "try_acquire_async", _always_allow)
    monkeypatch.setattr(password_reset_limiter, "try_acquire_async", _always_allow)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated DB state per test.

    Many tests commit inside services/routes. A rollback-only strategy leaks state
    (login attempts, employees, approvals, etc.) to subsequent tests and causes
    cascading failures. We clear all tables before and after each test.
    """
    async with TestSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f'DELETE FROM "{table.name}"'))
        await session.commit()

        yield session

        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f'DELETE FROM "{table.name}"'))
        await session.commit()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# Alias for tests that use async_client fixture name
@pytest_asyncio.fixture
async def async_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

import bcrypt as _bcrypt


async def make_employee(
    db: AsyncSession,
    email: str = "alice@example.com",
    password: str = "Password1",
    role: str = "employee",
    status: str = "active",
    manager_id: int | None = None,
) -> Employee:
    from app.models.organization import Organization
    from sqlalchemy import select

    # Ensure org 1 exists (used by default)
    result = await db.execute(select(Organization).where(Organization.org_id == 1))
    org = result.scalar_one_or_none()
    if not org:
        org = Organization(org_id=1, org_name="Test Org", manager_id=manager_id)
        db.add(org)
        await db.flush()
    elif manager_id and org.manager_id is None:
        org.manager_id = manager_id
        await db.flush()

    emp = Employee(
        email=email,
        first_name="Alice",
        last_name="Smith",
        password_hash=_bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=4)).decode(),
        role=role,
        employment_status=status,
        org_id=1,
        manager_id=manager_id,
    )
    db.add(emp)
    await db.flush()
    await db.refresh(emp)

    # If this employee is a manager, update org.manager_id
    if role == "manager":
        org.manager_id = emp.employee_id
        await db.flush()

    return emp


async def make_client(db: AsyncSession, name: str = "Acme Corp") -> Client:
    from decimal import Decimal
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


async def make_project(
    db: AsyncSession,
    client_id: int,
    manager_id: int,
    name: str = "Project Alpha",
    status: str = "active",
) -> Project:
    from decimal import Decimal
    import random, string
    code = "P-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    p = Project(
        client_id=client_id,
        project_name=name,
        project_code=code,
        status=status,
        start_date=date(2025, 1, 1),
        billing_rate=Decimal("120.00"),
        manager_id=manager_id,
        team_members=[manager_id],
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return p


async def make_entry(
    db: AsyncSession,
    employee_id: int,
    project_id: int,
    work_date: date,
    hours: float = 8.0,
) -> TimesheetEntry:
    from decimal import Decimal
    e = TimesheetEntry(
        employee_id=employee_id,
        project_id=project_id,
        work_date=work_date,
        hours_worked=Decimal(str(hours)),
        description="Test work",
        task_type="dev",
        billable_flag=True,
        status="draft",
    )
    db.add(e)
    await db.flush()
    await db.refresh(e)
    return e
