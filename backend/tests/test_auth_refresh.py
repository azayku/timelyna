"""Integration tests: POST /refresh — token rotation (task 1.20)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.auth_repository import AuthRepository
from tests.conftest import make_employee


async def _login(client: AsyncClient, email: str, password: str = "Password1") -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.cookies["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="refresh_ok@example.com")
    await db.commit()

    rt = await _login(client, "refresh_ok@example.com")
    resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": rt})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    # New refresh cookie issued
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_refresh_rotation_old_token_invalid(client: AsyncClient, db: AsyncSession):
    await make_employee(db, email="refresh_rotate@example.com")
    await db.commit()

    rt = await _login(client, "refresh_rotate@example.com")
    # Use the token once
    resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": rt})
    assert resp.status_code == 200

    # Reuse old token — must fail
    resp2 = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": rt})
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_revoked_token(client: AsyncClient, db: AsyncSession):
    emp = await make_employee(db, email="refresh_revoked@example.com")
    await db.commit()

    rt = await _login(client, "refresh_revoked@example.com")

    # Revoke via logout
    await client.post("/api/v1/auth/logout", cookies={"refresh_token": rt})

    resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": rt})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_expired_token(client: AsyncClient, db: AsyncSession):
    emp = await make_employee(db, email="refresh_expired@example.com")
    await db.commit()

    # Manually insert an already-expired refresh token
    import uuid, hashlib
    token = str(uuid.uuid4())
    repo = AuthRepository(db)
    expired_at = datetime.now(timezone.utc) - timedelta(days=1)
    await repo.create_refresh_token(emp.employee_id, token, expired_at)
    await db.commit()

    resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient, db: AsyncSession):
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401
