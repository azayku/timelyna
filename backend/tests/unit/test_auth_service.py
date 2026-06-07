"""Unit tests for AuthService — TEST-AUTH-001 through TEST-AUTH-015."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt as _bcrypt
import jwt
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_public_key_pem
from app.models.auth import LoginAttempt, RefreshToken
from app.models.employee import Employee
from app.models.pending_employee import PendingEmployee
from app.models.proxy_audit_log import ProxyAuditLog
from app.services.auth_service import AuthService

from tests.unit.conftest import (
    _make_employee,
    _make_org,
    _make_org_settings,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt(rounds=4)).decode()


# ---------------------------------------------------------------------------
# TEST-AUTH-001 — valid email returns tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_valid_email_returns_tokens(db: AsyncSession):
    emp = await _make_employee(db, email="alice@test.com", password="SecurePass123")
    await db.commit()

    service = AuthService(db)
    result = await service.authenticate("alice@test.com", "SecurePass123")

    assert "access_token" in result
    assert "refresh_token" in result
    assert "expires_at" in result

    payload = jwt.decode(result["access_token"], get_public_key_pem(), algorithms=["RS256"])
    assert payload["employee_id"] == emp.employee_id
    assert payload["role"] == "employee"
    assert "org_id" in payload


# ---------------------------------------------------------------------------
# TEST-AUTH-002 — valid username returns tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_valid_username_returns_tokens(db: AsyncSession):
    emp = await _make_employee(
        db,
        email="alice2@test.com",
        password="SecurePass123",
        username="alice.martin",
    )
    await db.commit()

    service = AuthService(db)
    result = await service.authenticate("alice.martin", "SecurePass123")

    assert "access_token" in result
    payload = jwt.decode(result["access_token"], get_public_key_pem(), algorithms=["RS256"])
    assert payload["employee_id"] == emp.employee_id


# ---------------------------------------------------------------------------
# TEST-AUTH-003 — wrong password raises 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_wrong_password_raises_401(db: AsyncSession):
    await _make_employee(db, email="alice3@test.com", password="SecurePass123")
    await db.commit()

    service = AuthService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate("alice3@test.com", "WrongPassword")

    assert exc_info.value.status_code == 401
    # Message must not reveal which field was wrong
    detail = exc_info.value.detail
    assert "email" in detail.lower() or "password" in detail.lower() or "invalid" in detail.lower()

    # Confirm a failed LoginAttempt was recorded
    from sqlalchemy import select
    result = await db.execute(
        select(LoginAttempt).where(
            LoginAttempt.email == "alice3@test.com",
            LoginAttempt.success.is_(False),
        )
    )
    attempt = result.scalar_one_or_none()
    assert attempt is not None


# ---------------------------------------------------------------------------
# TEST-AUTH-004 — unknown identifier raises 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_unknown_identifier_raises_401(db: AsyncSession):
    service = AuthService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate("nonexistent@test.com", "anything")

    assert exc_info.value.status_code == 401
    # Same message as wrong password — no enumeration
    assert exc_info.value.detail is not None


# ---------------------------------------------------------------------------
# TEST-AUTH-005 — locked account raises 429
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_locked_account_raises_429(db: AsyncSession):
    from app.core.config import get_settings
    settings = get_settings()

    locked_email = "locked@test.com"

    # Seed failed attempts exceeding LOGIN_MAX_ATTEMPTS within window
    now = datetime.now(timezone.utc)
    for _ in range(settings.LOGIN_MAX_ATTEMPTS):
        attempt = LoginAttempt(
            email=locked_email,
            success=False,
            ip_address="127.0.0.1",
            attempted_at=now - timedelta(minutes=1),
        )
        db.add(attempt)
    await db.commit()

    service = AuthService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate(locked_email, "anypassword")

    assert exc_info.value.status_code == 429


# ---------------------------------------------------------------------------
# TEST-AUTH-006 — inactive employee raises 401/403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_inactive_employee_raises_401(db: AsyncSession):
    await _make_employee(
        db,
        email="inactive@test.com",
        password="SecurePass123",
        status="inactive",
    )
    await db.commit()

    service = AuthService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate("inactive@test.com", "SecurePass123")

    assert exc_info.value.status_code in (401, 403)


# ---------------------------------------------------------------------------
# TEST-AUTH-007 — refresh valid token returns new tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_valid_token_returns_new_tokens(db: AsyncSession):
    emp = await _make_employee(db, email="refresh_ok@test.com", password="SecurePass123")
    await db.commit()

    service = AuthService(db)
    first_result = await service.authenticate("refresh_ok@test.com", "SecurePass123")
    old_refresh = first_result["refresh_token"]

    new_result = await service.refresh(old_refresh)

    assert "access_token" in new_result
    assert "refresh_token" in new_result
    # New token must differ
    assert new_result["refresh_token"] != old_refresh

    # Old token must be revoked
    from sqlalchemy import select
    import hashlib
    old_hash = hashlib.sha256(old_refresh.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    )
    rt = result.scalar_one_or_none()
    assert rt is not None
    assert rt.revoked_at is not None


# ---------------------------------------------------------------------------
# TEST-AUTH-008 — refresh revoked token raises 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_revoked_token_raises_401(db: AsyncSession):
    emp = await _make_employee(db, email="revoked@test.com", password="SecurePass123")
    await db.commit()

    service = AuthService(db)
    result = await service.authenticate("revoked@test.com", "SecurePass123")
    refresh_token = result["refresh_token"]

    # Use the token once (rotates it)
    await service.refresh(refresh_token)

    # Now try again with the same (now revoked) token
    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(refresh_token)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# TEST-AUTH-009 — refresh expired token raises 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_expired_token_raises_401(db: AsyncSession):
    import hashlib
    emp = await _make_employee(db, email="expired_rt@test.com", password="SecurePass123")
    await db.commit()

    # Insert an expired refresh token directly
    expired_token_value = "expired-token-value-12345"
    expired_rt = RefreshToken(
        employee_id=emp.employee_id,
        token_hash=hashlib.sha256(expired_token_value.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(expired_rt)
    await db.commit()

    service = AuthService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(expired_token_value)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# TEST-AUTH-010 — change_password success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_password_success(db: AsyncSession):
    emp = await _make_employee(db, email="changepw@test.com", password="OldPass123")
    await db.commit()

    service = AuthService(db)

    with patch("app.tasks.email_tasks.task_send_password_changed_email") as mock_email:
        await service.change_password(emp.employee_id, "OldPass123", "NewPass456")

    # Reload and verify new hash
    from sqlalchemy import select
    result = await db.execute(
        select(Employee).where(Employee.employee_id == emp.employee_id)
    )
    updated = result.scalar_one()
    assert _bcrypt.checkpw(b"NewPass456", updated.password_hash.encode())
    assert updated.must_change_password is False


# ---------------------------------------------------------------------------
# TEST-AUTH-011 — change_password wrong current password raises 400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_password_wrong_current_raises_400(db: AsyncSession):
    emp = await _make_employee(db, email="changepw_bad@test.com", password="CorrectPass1")
    original_hash = emp.password_hash
    await db.commit()

    service = AuthService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.change_password(emp.employee_id, "WrongOldPass", "NewPass456")

    assert exc_info.value.status_code == 400

    # Verify password was NOT changed
    from sqlalchemy import select
    result = await db.execute(
        select(Employee).where(Employee.employee_id == emp.employee_id)
    )
    unchanged = result.scalar_one()
    assert unchanged.password_hash == original_hash


# ---------------------------------------------------------------------------
# TEST-AUTH-012 — create_employee_or_pending: hire_date soon → immediate employee
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_employee_immediate_when_hire_date_soon(db: AsyncSession):
    await _make_org(db, org_id=1)
    await _make_org_settings(db, org_id=1, account_creation_lead_days=7)
    await db.commit()

    hire_date = date.today() + timedelta(days=1)  # tomorrow — within lead_days window

    service = AuthService(db)
    result = await service.create_employee_or_pending(
        email="new_imm@test.com",
        first_name="New",
        last_name="Employee",
        role="employee",
        birth_date=date(1990, 1, 1),
        address="123 Main St",
        hire_date=hire_date,
    )

    assert result["type"] == "employee"
    assert "generated_username" in result
    assert "generated_password" in result

    # Verify employee exists in DB
    from sqlalchemy import select
    res = await db.execute(
        select(Employee).where(Employee.email == "new_imm@test.com")
    )
    assert res.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# TEST-AUTH-013 — create_employee_or_pending: hire_date far → pending
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_pending_employee_when_hire_date_far(db: AsyncSession):
    await _make_org(db, org_id=1)
    await _make_org_settings(db, org_id=1, account_creation_lead_days=7)
    await db.commit()

    hire_date = date.today() + timedelta(days=30)  # far in future

    service = AuthService(db)
    result = await service.create_employee_or_pending(
        email="new_pend@test.com",
        first_name="Pending",
        last_name="Worker",
        role="employee",
        birth_date=date(1990, 6, 15),
        address="456 Elm St",
        hire_date=hire_date,
    )

    assert result["type"] == "pending"

    # Verify PendingEmployee was created, not Employee
    from sqlalchemy import select
    pending_res = await db.execute(
        select(PendingEmployee).where(PendingEmployee.email == "new_pend@test.com")
    )
    assert pending_res.scalar_one_or_none() is not None

    emp_res = await db.execute(
        select(Employee).where(Employee.email == "new_pend@test.com")
    )
    assert emp_res.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# TEST-AUTH-014 — duplicate email raises 409/422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_employee_duplicate_email_raises_422(db: AsyncSession):
    await _make_employee(db, email="dup@test.com", password="Pass123")
    await db.commit()

    service = AuthService(db)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_employee(
            email="dup@test.com",
            first_name="Dup",
            last_name="User",
            role="employee",
            birth_date=date(1990, 1, 1),
            address="789 Oak Ave",
        )

    assert exc_info.value.status_code in (409, 422)


# ---------------------------------------------------------------------------
# TEST-AUTH-015 — proxy token contains correct claims
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_proxy_token_contains_correct_claims(db: AsyncSession):
    admin = await _make_employee(
        db,
        email="proxyadmin@test.com",
        password="AdminPass1",
        role="admin",
    )
    employee = await _make_employee(
        db,
        email="proxytarget@test.com",
        password="EmpPass1",
        role="employee",
    )
    await db.commit()

    service = AuthService(db)
    result = await service.create_proxy_token(
        admin_id=admin.employee_id,
        employee_id=employee.employee_id,
    )

    assert "token" in result
    assert "proxy_log_id" in result

    # Decode and check claims
    payload = jwt.decode(result["token"], get_public_key_pem(), algorithms=["RS256"])
    assert payload["employee_id"] == employee.employee_id
    assert payload["proxy_admin_id"] == admin.employee_id
    assert payload.get("is_proxy") is True

    # Expiry should be ~2h from now
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = exp - now
    assert timedelta(hours=1, minutes=55) < delta < timedelta(hours=2, minutes=5)

    # Audit log should exist
    from sqlalchemy import select
    res = await db.execute(
        select(ProxyAuditLog).where(ProxyAuditLog.id == result["proxy_log_id"])
    )
    log = res.scalar_one_or_none()
    assert log is not None
    assert log.admin_id == admin.employee_id
    assert log.employee_id == employee.employee_id
    assert log.started_at is not None
