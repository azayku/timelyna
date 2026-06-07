"""Integration tests: password change + reset (tasks 1.22, 1.23)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import make_employee


def _auth_headers(employee_id: int, email: str, role: str = "employee") -> dict:
    token = create_access_token({"sub": email, "employee_id": employee_id, "org_id": 1, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Task 1.22 — POST /password/change
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, db: AsyncSession):
    emp = await make_employee(db, email="chpw_ok@example.com", password="OldPass1")
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "OldPass1", "new_password": "NewPass2"},
        headers=_auth_headers(emp.employee_id, emp.email),
    )
    assert resp.status_code == 204

    # Old password no longer works
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "chpw_ok@example.com", "password": "OldPass1"}
    )
    assert login_resp.status_code == 401

    # New password works
    login_resp2 = await client.post(
        "/api/v1/auth/login", json={"email": "chpw_ok@example.com", "password": "NewPass2"}
    )
    assert login_resp2.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, db: AsyncSession):
    emp = await make_employee(db, email="chpw_bad@example.com", password="OldPass1")
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "WrongOld9", "new_password": "NewPass2"},
        headers=_auth_headers(emp.employee_id, emp.email),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_change_password_invalidates_refresh_tokens(client: AsyncClient, db: AsyncSession):
    emp = await make_employee(db, email="chpw_rt@example.com", password="OldPass1")
    await db.commit()

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "chpw_rt@example.com", "password": "OldPass1"}
    )
    rt = login_resp.cookies["refresh_token"]

    await client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "OldPass1", "new_password": "NewPass2"},
        headers=_auth_headers(emp.employee_id, emp.email),
    )

    # Old refresh token must be revoked
    refresh_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": rt})
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password_weak_new_password(client: AsyncClient, db: AsyncSession):
    emp = await make_employee(db, email="chpw_weak@example.com", password="OldPass1")
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "OldPass1", "new_password": "weak"},
        headers=_auth_headers(emp.employee_id, emp.email),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Task 1.23 — POST /password/reset-request + /password/reset
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reset_request_always_200(client: AsyncClient, db: AsyncSession):
    # Known email
    await make_employee(db, email="reset_known@example.com")
    await db.commit()
    resp = await client.post(
        "/api/v1/auth/password/reset-request", json={"email": "reset_known@example.com"}
    )
    assert resp.status_code == 200

    # Unknown email — still 200 (no enumeration)
    resp2 = await client.post(
        "/api/v1/auth/password/reset-request", json={"email": "nobody_reset@example.com"}
    )
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient, db: AsyncSession):
    import secrets
    from datetime import datetime, timedelta, timezone
    from app.repositories.auth_repository import AuthRepository

    emp = await make_employee(db, email="reset_flow@example.com", password="OldPass1")
    await db.commit()

    token = secrets.token_urlsafe(32)
    repo = AuthRepository(db)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await repo.create_password_reset_token(emp.employee_id, token, expires_at)
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "NewPass2"},
    )
    assert resp.status_code == 204

    # New password works
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "reset_flow@example.com", "password": "NewPass2"}
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_token_single_use(client: AsyncClient, db: AsyncSession):
    import secrets
    from datetime import datetime, timedelta, timezone
    from app.repositories.auth_repository import AuthRepository

    emp = await make_employee(db, email="reset_once@example.com", password="OldPass1")
    await db.commit()

    token = secrets.token_urlsafe(32)
    repo = AuthRepository(db)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await repo.create_password_reset_token(emp.employee_id, token, expires_at)
    await db.commit()

    await client.post("/api/v1/auth/password/reset", json={"token": token, "new_password": "NewPass2"})

    # Second use must fail
    resp2 = await client.post(
        "/api/v1/auth/password/reset", json={"token": token, "new_password": "AnotherPass3"}
    )
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_reset_invalid_token(client: AsyncClient, db: AsyncSession):
    resp = await client.post(
        "/api/v1/auth/password/reset", json={"token": "bogus-token", "new_password": "NewPass2"}
    )
    assert resp.status_code == 400
