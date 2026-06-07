"""DB access layer for pending_employees table."""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pending_employee import PendingEmployee


class PendingEmployeeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        first_name: str,
        last_name: str,
        email: str,
        role: str,
        hire_date: date,
        account_creation_date: date,
        manager_id: Optional[int] = None,
        birth_date: Optional[date] = None,
        address: Optional[str] = None,
    ) -> PendingEmployee:
        p = PendingEmployee(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            hire_date=hire_date,
            account_creation_date=account_creation_date,
            manager_id=manager_id,
            birth_date=birth_date,
            address=address,
        )
        self.db.add(p)
        await self.db.flush()
        await self.db.refresh(p)
        return p

    async def get_pending_due(self, today: date) -> list[PendingEmployee]:
        """Return all pending employees whose account_creation_date <= today."""
        result = await self.db.execute(
            select(PendingEmployee).where(PendingEmployee.account_creation_date <= today)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[PendingEmployee]:
        result = await self.db.execute(
            select(PendingEmployee).order_by(PendingEmployee.account_creation_date)
        )
        return list(result.scalars().all())

    async def get_by_id(self, pending_id: int) -> Optional[PendingEmployee]:
        result = await self.db.execute(
            select(PendingEmployee).where(PendingEmployee.id == pending_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, pending_id: int) -> None:
        await self.db.execute(
            delete(PendingEmployee).where(PendingEmployee.id == pending_id)
        )
