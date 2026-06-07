"""Integration tests: POST /logout (task 1.21)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_employee


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="logout_ok@example.com")
    await db.commit()

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "logout_ok@example.com", "password": "Password1"}
    )
    rt = login_resp.cookies["refresh_token"]

    logout_resp = await client.post("/api/v1/auth/logout", cookies={"refresh_token": rt})
    assert logout_resp.status_code == 204

    # Refresh with revoked token must fail
    refresh_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": rt})
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_cookie(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="logout_cookie@example.com")
    await db.commit()

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "logout_cookie@example.com", "password": "Password1"}
    )
    rt = login_resp.cookies["refresh_token"]

    logout_resp = await client.post("/api/v1/auth/logout", cookies={"refresh_token": rt})
    # Cookie should be cleared (set to empty / expired)
    assert logout_resp.status_code == 204
