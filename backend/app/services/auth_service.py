"""AuthService — business logic for all authentication operations."""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token
from app.repositories.auth_repository import AuthRepository

logger = logging.getLogger(__name__)

_BCRYPT_ROUNDS = 12

# Pre-computed dummy hash used for constant-time comparison when user not found
_DUMMY_HASH = _bcrypt.hashpw(b"dummy-password-for-timing", _bcrypt.gensalt(rounds=4)).decode()


def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuthRepository(db)
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Task 1.9 — authenticate (login)
    # ------------------------------------------------------------------

    async def authenticate(
        self, identifier: str, password: str, ip_address: Optional[str] = None
    ) -> dict:
        """Validate credentials (email or username), enforce lockout, return tokens."""
        # Check lockout before touching the employee record (no enumeration)
        recent_failures = await self.repo.count_recent_failures(
            identifier, self.settings.LOGIN_WINDOW_MINUTES
        )
        if recent_failures >= self.settings.LOGIN_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account locked due to too many failed attempts. Try again later.",
            )

        # Try to find employee by email OR username
        employee = await self.repo.get_employee_by_email(identifier)
        if not employee:
            employee = await self.repo.get_employee_by_username(identifier)

        # Always run bcrypt to prevent timing attacks
        candidate_hash = employee.password_hash if employee else _DUMMY_HASH
        password_ok = _verify_password(password, candidate_hash)

        if not employee or not password_ok:
            await self.repo.record_login_attempt(identifier, success=False, ip_address=ip_address)
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email/username or password",
            )

        if employee.employment_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        await self.repo.record_login_attempt(identifier, success=True, ip_address=ip_address)

        access_token = create_access_token({
            "sub": employee.email,
            "employee_id": employee.employee_id,
            "org_id": employee.org_id,
            "role": employee.role,
            "must_change_password": employee.must_change_password,
        })
        refresh_token, expires_at = await self._create_refresh_token(employee.employee_id)
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }

    # ------------------------------------------------------------------
    # Task 1.10 — refresh (token rotation)
    # ------------------------------------------------------------------

    async def refresh(self, token: str) -> dict:
        """Validate refresh token, rotate it, return new tokens."""
        rt = await self.repo.get_refresh_token(token)

        if rt is None or rt.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
            )

        now = datetime.now(timezone.utc)
        expires = rt.expires_at if rt.expires_at.tzinfo else rt.expires_at.replace(tzinfo=timezone.utc)
        if expires < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        # Rotate — invalidate old token
        await self.repo.revoke_refresh_token(token)

        employee = await self.repo.get_employee_by_id(rt.employee_id)
        if not employee or employee.employment_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        access_token = create_access_token({
            "sub": employee.email,
            "employee_id": employee.employee_id,
            "org_id": employee.org_id,
            "role": employee.role,
            "must_change_password": employee.must_change_password,
        })
        new_refresh_token, new_expires_at = await self._create_refresh_token(employee.employee_id)
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_at": new_expires_at,
        }

    # ------------------------------------------------------------------
    # Task 1.11 — revoke_token (logout)
    # ------------------------------------------------------------------

    async def revoke_token(self, token: str) -> None:
        """Revoke a refresh token (logout)."""
        rt = await self.repo.get_refresh_token(token)
        if rt is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        await self.repo.revoke_refresh_token(token)
        await self.db.commit()

    # ------------------------------------------------------------------
    # Task 1.12 — change_password
    # ------------------------------------------------------------------

    async def change_password(
        self, employee_id: int, current_password: str, new_password: str
    ) -> None:
        """Verify current password, update hash, invalidate all refresh tokens."""
        employee = await self.repo.get_employee_by_id(employee_id)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not _verify_password(current_password, employee.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        new_hash = _hash_password(new_password)
        await self.repo.update_employee(employee_id, password_hash=new_hash, must_change_password=False)
        await self.repo.revoke_all_refresh_tokens(employee_id)
        await self.db.commit()

        # Send confirmation email async (fire-and-forget)
        try:
            from app.tasks.email_tasks import task_send_password_changed_email
            lang = getattr(employee, 'preferred_language', 'fr')
            task_send_password_changed_email(employee.email, lang=lang)
        except Exception:
            logger.warning("Auth email failed", exc_info=True)

    # ------------------------------------------------------------------
    # Task 1.13 — request_reset (always 200)
    # ------------------------------------------------------------------

    async def request_reset(self, email: str) -> None:
        """Send password reset email. Always returns 200 to prevent enumeration."""
        employee = await self.repo.get_employee_by_email(email)
        if not employee:
            return  # Silent — no enumeration

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await self.repo.create_password_reset_token(employee.employee_id, token, expires_at)
        await self.db.commit()

        reset_link = f"{self.settings.FRONTEND_URL}/reset-password?token={token}"
        try:
            from app.tasks.email_tasks import task_send_reset_email
            lang = getattr(employee, 'preferred_language', 'fr')
            task_send_reset_email(
                employee.email, reset_link,
                first_name=employee.first_name,
                last_name=employee.last_name,
                lang=lang,
            )
        except Exception:
            logger.warning("Password reset email failed", exc_info=True)

    # ------------------------------------------------------------------
    # Task 1.14 — reset_password
    # ------------------------------------------------------------------

    async def reset_password(self, token: str, new_password: str) -> None:
        """Validate reset token, set new password, invalidate token."""
        prt = await self.repo.get_password_reset_token(token)

        if prt is None or prt.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or already used reset token",
            )

        now = datetime.now(timezone.utc)
        expires = prt.expires_at if prt.expires_at.tzinfo else prt.expires_at.replace(tzinfo=timezone.utc)
        if expires < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired",
            )

        new_hash = _hash_password(new_password)
        await self.repo.update_employee(prt.employee_id, password_hash=new_hash)
        await self.repo.mark_reset_token_used(token)
        await self.repo.revoke_all_refresh_tokens(prt.employee_id)
        await self.db.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _create_refresh_token(self, employee_id: int) -> tuple[str, datetime]:
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.repo.create_refresh_token(employee_id, token, expires_at)
        return token, expires_at

    # ------------------------------------------------------------------
    # Admin helpers
    # ------------------------------------------------------------------

    async def create_employee(
        self,
        email: str,
        first_name: str,
        last_name: str,
        role: str,
        manager_id: Optional[int] = None,
        birth_date=None,
        address: Optional[str] = None,
    ):
        from datetime import date as _date
        from app.utils.username import generate_username, ensure_unique_username, generate_default_password

        # Validate birth_date
        if birth_date is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La date de naissance est obligatoire",
            )
        if birth_date > _date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La date de naissance ne peut pas être dans le futur",
            )

        # Validate address
        if not address or not address.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="L'adresse est obligatoire",
            )

        existing = await self.repo.get_employee_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )

        # Collect existing usernames for uniqueness check
        employees, _ = await self.repo.list_employees(offset=0, limit=10000)
        existing_usernames: set[str] = {
            e.username for e in employees if e.username is not None
        }

        # Generate username and default password
        base_username = generate_username(first_name, last_name)
        username = ensure_unique_username(base_username, existing_usernames)
        default_password = generate_default_password(username, birth_date)
        password_hash = _hash_password(default_password)

        employee = await self.repo.create_employee(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            role=role,
            manager_id=manager_id,
            username=username,
            birth_date=birth_date,
            address=address,
            must_change_password=True,
        )

        await self.db.commit()
        await self.db.refresh(employee)

        # Store generated username on the returned object for the API to expose
        employee._generated_username = username  # type: ignore[attr-defined]
        employee._generated_password = default_password  # type: ignore[attr-defined]

        return employee

    # ------------------------------------------------------------------
    # US-08 — activate / deactivate
    # ------------------------------------------------------------------

    async def deactivate_employee(self, employee_id: int) -> None:
        """Set status to inactive and revoke all active sessions."""
        await self.repo.update_employee(employee_id, employment_status="inactive")
        await self.repo.revoke_all_refresh_tokens(employee_id)
        await self.db.commit()

    async def activate_employee(self, employee_id: int) -> None:
        """Re-activate a previously deactivated employee."""
        await self.repo.update_employee(employee_id, employment_status="active")
        await self.db.commit()

    async def schedule_deactivation(self, employee_id: int, scheduled_at: datetime) -> None:
        """Store deferred deactivation date; send warning email if ≤ 7 days away."""
        await self.repo.update_employee(employee_id, deactivation_scheduled_at=scheduled_at)
        await self.db.commit()

        # Fire-and-forget warning email if within 7 days
        delta = scheduled_at - datetime.now(timezone.utc)
        if delta.days <= 7:
            employee = await self.repo.get_employee_by_id(employee_id)
            if employee:
                try:
                    from app.tasks.email_tasks import task_send_deactivation_warning_email
                    lang = getattr(employee, 'preferred_language', 'fr')
                    task_send_deactivation_warning_email(
                        employee.email, scheduled_at.isoformat(), lang=lang
                    )
                except Exception:
                    logger.warning("Deactivation warning email failed", exc_info=True)

    async def cancel_scheduled_deactivation(self, employee_id: int) -> None:
        """Remove the scheduled deactivation date."""
        await self.repo.update_employee(employee_id, deactivation_scheduled_at=None)
        await self.db.commit()

    # ------------------------------------------------------------------
    # 12d.4 — create_proxy_token
    # ------------------------------------------------------------------

    async def create_proxy_token(self, admin_id: int, employee_id: int) -> dict:
        """Create a proxy JWT for admin impersonating an employee."""
        from app.models.proxy_audit_log import ProxyAuditLog

        jti = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Build token with 2h expiry
        token = create_access_token({
            "sub": str(employee_id),
            "employee_id": employee_id,
            "is_proxy": True,
            "proxy_admin_id": admin_id,
            "jti": jti,
            "exp": now + timedelta(hours=2),
        })

        # Insert audit log row
        log = ProxyAuditLog(
            admin_id=admin_id,
            employee_id=employee_id,
            started_at=now,
            token_jti=jti,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        await self.db.commit()

        return {"token": token, "proxy_log_id": log.id}

    # ------------------------------------------------------------------
    # 12d.5 — end_proxy_session
    # ------------------------------------------------------------------

    async def end_proxy_session(self, proxy_log_id: int, entries_created: int = 0) -> None:
        """Record end time and entry count on the proxy audit log."""
        from sqlalchemy import update as _update
        from app.models.proxy_audit_log import ProxyAuditLog

        await self.db.execute(
            _update(ProxyAuditLog)
            .where(ProxyAuditLog.id == proxy_log_id)
            .values(ended_at=datetime.now(timezone.utc), entries_created=entries_created)
        )
        await self.db.commit()

    # ------------------------------------------------------------------
    # 12d.21 — create_employee_or_pending
    # ------------------------------------------------------------------

    async def create_employee_or_pending(
        self,
        email: str,
        first_name: str,
        last_name: str,
        role: str,
        manager_id: Optional[int] = None,
        birth_date=None,
        address: Optional[str] = None,
        hire_date=None,
    ) -> dict:
        """Create employee immediately or as pending based on hire_date and lead_days."""
        from datetime import date as _date, timedelta as _td
        from sqlalchemy import select as _sel
        from app.models.org_settings import OrgSettings
        from app.models.pending_employee import PendingEmployee

        today = _date.today()

        # Fetch lead_days from org settings
        result = await self.db.execute(_sel(OrgSettings).where(OrgSettings.org_id == 1))
        org_settings = result.scalar_one_or_none()
        lead_days = getattr(org_settings, "account_creation_lead_days", 2) if org_settings else 2

        # Normalise hire_date to a plain date
        if hire_date is not None and hasattr(hire_date, "date"):
            hire_date = hire_date.date()

        # Determine if deferred: account_creation_date = hire_date - lead_days > today
        if hire_date is not None:
            account_creation_date = hire_date - _td(days=lead_days)
            deferred = account_creation_date > today
        else:
            deferred = False

        if deferred:
            pending = PendingEmployee(
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
                manager_id=manager_id,
                birth_date=birth_date,
                address=address,
                hire_date=hire_date,
                account_creation_date=account_creation_date,
            )
            self.db.add(pending)
            await self.db.flush()
            await self.db.refresh(pending)
            await self.db.commit()
            return {
                "type": "pending",
                "id": pending.id,
                "first_name": pending.first_name,
                "last_name": pending.last_name,
                "email": pending.email,
                "role": pending.role,
                "hire_date": str(pending.hire_date),
                "account_creation_date": str(pending.account_creation_date),
            }
        else:
            employee = await self.create_employee(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                manager_id=manager_id,
                birth_date=birth_date,
                address=address,
            )
            return {
                "type": "employee",
                "id": employee.employee_id,
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "email": employee.email,
                "role": employee.role,
                "generated_username": getattr(employee, "_generated_username", None),
                "generated_password": getattr(employee, "_generated_password", None),
            }
