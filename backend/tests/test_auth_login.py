"""Integration tests: POST /login (task 1.18)."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_employee


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="login_ok@example.com", password="Password1")
    await db.commit()

    resp = await client.post("/api/v1/auth/login", json={"email": "login_ok@example.com", "password": "Password1"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    # refresh token cookie must be set
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="login_bad@example.com", password="Password1")
    await db.commit()

    resp = await client.post("/api/v1/auth/login", json={"email": "login_bad@example.com", "password": "WrongPass9"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient, db: AsyncSession):
    resp = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "Password1"})
    assert resp.status_code == 401
    # Same message — no enumeration
    assert resp.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_inactive_account(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="inactive@example.com", password="Password1", status="inactive")
    await db.commit()

    resp = await client.post("/api/v1/auth/login", json={"email": "inactive@example.com", "password": "Password1"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_no_plaintext_password_in_response(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="noplain@example.com", password="Password1")
    await db.commit()

    resp = await client.post("/api/v1/auth/login", json={"email": "noplain@example.com", "password": "Password1"})
    assert "Password1" not in resp.text
    assert "password" not in resp.json()
