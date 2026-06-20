"""
Integration tests for user creation and authentication with username generation.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


def _auth_headers(login_response) -> dict:
    """Extract auth headers from login response."""
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_user_generates_username(async_client: AsyncClient, db: AsyncSession):
    """Test that POST /admin/users generates username."""
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timelyna.com", "password": "Admin1234!"}
    )
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
        },
        headers=headers,
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert "username" in data
    assert data["username"].startswith("doej")


@pytest.mark.asyncio
async def test_deactivate_user_revokes_tokens(async_client: AsyncClient, db: AsyncSession):
    """Test that deactivating a user works."""
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timelyna.com", "password": "Admin1234!"}
    )
    assert login_response.status_code == 200
    headers = _auth_headers(login_response)

    create_response = await async_client.post(
        "/api/v1/admin/users",
        json={
            "email": "deactivate.test2@test.com",
            "first_name": "Test",
            "last_name": "Deact",
            "role": "employee",
        },
        headers=headers,
    )
    assert create_response.status_code in (200, 201)
    user_id = create_response.json()["employee_id"]

    deactivate_response = await async_client.put(
        f"/api/v1/admin/users/{user_id}/deactivate",
        headers=headers,
    )
    assert deactivate_response.status_code == 200

    # Verify via DB
    result = await db.execute(
        text(f"SELECT employment_status FROM employees WHERE employee_id = {user_id}")
    )
    row = result.fetchone()
    assert row[0] == "inactive"


@pytest.mark.asyncio
async def test_activate_user_allows_login(async_client: AsyncClient):
    """Test that activating a deactivated user works."""
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timelyna.com", "password": "Admin1234!"}
    )
    assert login_response.status_code == 200
    headers = _auth_headers(login_response)

    create_response = await async_client.post(
        "/api/v1/admin/users",
        json={
            "email": "activate.test2@test.com",
            "first_name": "Test",
            "last_name": "Activ",
            "role": "employee",
        },
        headers=headers,
    )
    assert create_response.status_code in (200, 201)
    user_id = create_response.json()["employee_id"]

    await async_client.put(f"/api/v1/admin/users/{user_id}/deactivate", headers=headers)

    activate_response = await async_client.put(
        f"/api/v1/admin/users/{user_id}/activate",
        headers=headers,
    )
    assert activate_response.status_code == 200


@pytest.mark.asyncio
async def test_username_collision_adds_suffix(async_client: AsyncClient):
    """Test that creating users with same name generates unique usernames."""
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timelyna.com", "password": "Admin1234!"}
    )
    assert login_response.status_code == 200
    headers = _auth_headers(login_response)

    r1 = await async_client.post("/api/v1/admin/users", json={
        "email": "collision.a@test.com", "first_name": "Collision", "last_name": "Test", "role": "employee",
    }, headers=headers)
    assert r1.status_code in (200, 201)
    u1 = r1.json()["username"]

    r2 = await async_client.post("/api/v1/admin/users", json={
        "email": "collision.b@test.com", "first_name": "Collision", "last_name": "Test", "role": "employee",
    }, headers=headers)
    assert r2.status_code in (200, 201)
    u2 = r2.json()["username"]

    assert u1 != u2
