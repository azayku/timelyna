"""Integration tests: rate limiting / lockout (task 1.19)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_employee


@pytest.mark.asyncio
async def test_lockout_after_five_failures(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="lockout@example.com", password="Password1")
    await db.commit()

    # 5 failed attempts
    for _ in range(5):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "lockout@example.com", "password": "WrongPass9"},
        )
        assert resp.status_code == 401

    # 6th attempt — should be locked out (429)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "lockout@example.com", "password": "Password1"},
    )
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_lockout_applies_to_unknown_email(client: AsyncClient, db: AsyncSession):
    """Lockout check runs before employee lookup — prevents enumeration."""
    email = "ghost_lockout@example.com"
    for _ in range(5):
        await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass9"})

    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass9"})
    assert resp.status_code == 429
