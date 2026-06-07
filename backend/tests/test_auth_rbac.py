"""Integration tests: RBAC — employee accessing manager route returns 403 (task 1.24)."""
from __future__ import annotations

import pytest
from fastapi import APIRouter, Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, require_role
from app.main import app
from tests.conftest import make_employee

# Register a test-only route that requires "manager" role
_test_router = APIRouter()


@_test_router.get("/api/v1/test/manager-only")
async def manager_only(_: dict = Depends(require_role("manager"))):
    return {"ok": True}


app.include_router(_test_router)


def _token(employee_id: int, email: str, role: str) -> str:
    return create_access_token({"sub": email, "employee_id": employee_id, "org_id": 1, "role": role})


@pytest.mark.asyncio
async def test_employee_cannot_access_manager_route(client: AsyncClient, db: AsyncSession):
    emp = await make_employee(db, email="rbac_emp@example.com", role="employee")
    await db.commit()

    resp = await client.get(
        "/api/v1/test/manager-only",
        headers={"Authorization": f"Bearer {_token(emp.employee_id, emp.email, 'employee')}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_manager_can_access_manager_route(client: AsyncClient, db: AsyncSession):
    mgr = await make_employee(db, email="rbac_mgr@example.com", role="manager")
    await db.commit()

    resp = await client.get(
        "/api/v1/test/manager-only",
        headers={"Authorization": f"Bearer {_token(mgr.employee_id, mgr.email, 'manager')}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_can_access_any_route(client: AsyncClient, db: AsyncSession):
    admin = await make_employee(db, email="rbac_admin@example.com", role="admin")
    await db.commit()

    resp = await client.get(
        "/api/v1/test/manager-only",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_protected_route(client: AsyncClient, db: AsyncSession):
    resp = await client.get("/api/v1/test/manager-only")
    assert resp.status_code == 401
