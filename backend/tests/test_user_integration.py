"""
Integration tests for user creation and authentication with username generation.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from tests.conftest import make_employee


def _auth_headers(login_response) -> dict:
    """Extract auth headers from login response."""
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _login_as_admin(async_client: AsyncClient, db: AsyncSession):
    await make_employee(
        db,
        email="admin@timelyna.com",
        password="Admin1234!",
        role="admin",
    )
    await db.commit()
    return await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timelyna.com", "password": "Admin1234!"},
    )


@pytest.mark.asyncio
async def test_create_user_generates_username(async_client: AsyncClient, db: AsyncSession):
    """Test that POST /admin/users generates username."""
    login_response = await _login_as_admin(async_client, db)
    assert login_response.status_code == 200
    headers = _auth_headers(login_response)

    response = await async_client.post(
        "/api/v1/admin/users",
        json={
            "email": "john.doe.gen@test.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "employee",
            "birth_date": "1990-05-15",
            "address": "10 rue de Lyon, Lyon",
        },
        headers=headers,
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert "generated_username" in data
    assert data["generated_username"].startswith("doej")


@pytest.mark.asyncio
async def test_deactivate_user_revokes_tokens(async_client: AsyncClient, db: AsyncSession):
    """Test that deactivating a user works."""
    login_response = await _login_as_admin(async_client, db)
    assert login_response.status_code == 200
    headers = _auth_headers(login_response)

    create_response = await async_client.post(
        "/api/v1/admin/users",
        json={
            "email": "deactivate.test2@test.com",
            "first_name": "Test",
            "last_name": "Deact",
            "role": "employee",
            "birth_date": "1991-02-10",
            "address": "12 rue Victor Hugo, Paris",
        },
        headers=headers,
    )
    assert create_response.status_code in (200, 201)
    user_id = create_response.json()["id"]

    deactivate_response = await async_client.put(
        f"/api/v1/admin/users/{user_id}/deactivate",
        headers=headers,
    )
    assert deactivate_response.status_code == 204

    # Verify via DB
    result = await db.execute(
        text(f"SELECT employment_status FROM employees WHERE employee_id = {user_id}")
    )
    row = result.fetchone()
    assert row[0] == "inactive"


@pytest.mark.asyncio
async def test_activate_user_allows_login(async_client: AsyncClient, db: AsyncSession):
    """Test that activating a deactivated user works."""
    login_response = await _login_as_admin(async_client, db)
    assert login_response.status_code == 200
    headers = _auth_headers(login_response)

    create_response = await async_client.post(
        "/api/v1/admin/users",
        json={
            "email": "activate.test2@test.com",
            "first_name": "Test",
            "last_name": "Activ",
            "role": "employee",
            "birth_date": "1992-03-11",
            "address": "8 avenue Foch, Lille",
        },
        headers=headers,
    )
    assert create_response.status_code in (200, 201)
    user_id = create_response.json()["id"]

    await async_client.put(f"/api/v1/admin/users/{user_id}/deactivate", headers=headers)

    activate_response = await async_client.put(
        f"/api/v1/admin/users/{user_id}/activate",
        headers=headers,
    )
    assert activate_response.status_code == 204


@pytest.mark.asyncio
async def test_username_collision_adds_suffix(async_client: AsyncClient, db: AsyncSession):
    """Test that creating users with same name generates unique usernames."""
    login_response = await _login_as_admin(async_client, db)
    assert login_response.status_code == 200
    headers = _auth_headers(login_response)

    r1 = await async_client.post("/api/v1/admin/users", json={
        "email": "collision.a@test.com", "first_name": "Collision", "last_name": "Test", "role": "employee",
        "birth_date": "1993-04-12", "address": "3 rue de la Paix, Nantes",
    }, headers=headers)
    assert r1.status_code in (200, 201)
    u1 = r1.json()["generated_username"]

    r2 = await async_client.post("/api/v1/admin/users", json={
        "email": "collision.b@test.com", "first_name": "Collision", "last_name": "Test", "role": "employee",
        "birth_date": "1994-05-13", "address": "5 rue Nationale, Toulouse",
    }, headers=headers)
    assert r2.status_code in (200, 201)
    u2 = r2.json()["generated_username"]

    assert u1 != u2
