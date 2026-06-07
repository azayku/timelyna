"""DB access layer for auth-related tables."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import LoginAttempt, PasswordResetToken, RefreshToken
from app.models.employee import Employee


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Employee
    # ------------------------------------------------------------------

    async def get_employee_by_email(self, email: str) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(Employee.email == email, Employee.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_employee_by_username(self, username: str) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(Employee.username == username, Employee.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_employee_by_id(self, employee_id: int) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(
                Employee.employee_id == employee_id, Employee.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def create_employee(self, **kwargs) -> Employee:
        emp = Employee(**kwargs)
        self.db.add(emp)
        await self.db.flush()
        await self.db.refresh(emp)
        return emp

    async def update_employee(self, employee_id: int, **kwargs) -> None:
        await self.db.execute(
            update(Employee).where(Employee.employee_id == employee_id).values(**kwargs)
        )

    async def list_employees(self, offset: int = 0, limit: int = 20) -> tuple[list[Employee], int]:
        count_result = await self.db.execute(
            select(func.count()).select_from(Employee).where(Employee.deleted_at.is_(None))
        )
        total = count_result.scalar_one()
        result = await self.db.execute(
            select(Employee)
            .where(Employee.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
            .order_by(Employee.employee_id)
        )
        return list(result.scalars().all()), total

    # ------------------------------------------------------------------
    # Refresh tokens
    # ------------------------------------------------------------------

    async def create_refresh_token(self, employee_id: int, token: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(
            employee_id=employee_id,
            token_hash=_sha256(token),
            expires_at=expires_at,
        )
        self.db.add(rt)
        await self.db.flush()
        return rt

    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == _sha256(token))
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == _sha256(token))
            .values(revoked_at=datetime.now(timezone.utc))
        )

    async def revoke_all_refresh_tokens(self, employee_id: int) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.employee_id == employee_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )

    # ------------------------------------------------------------------
    # Login attempts
    # ------------------------------------------------------------------

    async def record_login_attempt(
        self, email: str, success: bool, ip_address: Optional[str] = None
    ) -> None:
        attempt = LoginAttempt(email=email, success=success, ip_address=ip_address)
        self.db.add(attempt)
        await self.db.flush()

    async def count_recent_failures(self, email: str, window_minutes: int) -> int:
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        result = await self.db.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.email == email,
                LoginAttempt.success.is_(False),
                LoginAttempt.attempted_at >= since,
            )
        )
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Password reset tokens
    # ------------------------------------------------------------------

    async def create_password_reset_token(
        self, employee_id: int, token: str, expires_at: datetime
    ) -> PasswordResetToken:
        prt = PasswordResetToken(
            employee_id=employee_id,
            token_hash=_sha256(token),
            expires_at=expires_at,
        )
        self.db.add(prt)
        await self.db.flush()
        return prt

    async def get_password_reset_token(self, token: str) -> Optional[PasswordResetToken]:
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == _sha256(token)
            )
        )
        return result.scalar_one_or_none()

    async def mark_reset_token_used(self, token: str) -> None:
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.token_hash == _sha256(token))
            .values(used_at=datetime.now(timezone.utc))
        )
