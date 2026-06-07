"""Tests: création employé — validation birth_date et address (spec 12c.9)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import make_employee


def _admin_token(employee_id: int, email: str) -> dict:
    token = create_access_token({
        "sub": email,
        "employee_id": employee_id,
        "org_id": 1,
        "role": "admin",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_employee_without_birth_date_returns_422(
    client: AsyncClient, db: AsyncSession
):
    admin = await make_employee(db, email="admin_bd@example.com", role="admin")
    await db.commit()

    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "newuser_nobd@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "role": "employee",
            "address": "12 rue de la Paix, Paris",
            # birth_date absent
        },
        headers=_admin_token(admin.employee_id, admin.email),
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_create_employee_without_address_returns_422(
    client: AsyncClient, db: AsyncSession
):
    admin = await make_employee(db, email="admin_addr@example.com", role="admin")
    await db.commit()

    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "newuser_noaddr@example.com",
            "first_name": "Marie",
            "last_name": "Martin",
            "role": "employee",
            "birth_date": "1990-05-15",
            # address absent
        },
        headers=_admin_token(admin.employee_id, admin.email),
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_create_employee_with_future_birth_date_returns_422(
    client: AsyncClient, db: AsyncSession
):
    from datetime import date, timedelta
    admin = await make_employee(db, email="admin_future@example.com", role="admin")
    await db.commit()

    future = str(date.today() + timedelta(days=365))
    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "newuser_future@example.com",
            "first_name": "Paul",
            "last_name": "Futur",
            "role": "employee",
            "birth_date": future,
            "address": "1 avenue du Futur",
        },
        headers=_admin_token(admin.employee_id, admin.email),
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_create_employee_success_with_all_fields(
    client: AsyncClient, db: AsyncSession
):
    admin = await make_employee(db, email="admin_ok@example.com", role="admin")
    await db.commit()

    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "newuser_ok@example.com",
            "first_name": "Sophie",
            "last_name": "Bernard",
            "role": "employee",
            "birth_date": "1992-03-20",
            "address": "5 rue des Lilas, Lyon",
        },
        headers=_admin_token(admin.employee_id, admin.email),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["address"] == "5 rue des Lilas, Lyon"
