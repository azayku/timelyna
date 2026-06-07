"""EmployeeRepository — DB access for employees."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee


class EmployeeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, employee_id: int) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(
                Employee.employee_id == employee_id,
                Employee.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(
                Employee.email == email,
                Employee.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_active(self, skip: int = 0, limit: int = 20) -> list[Employee]:
        result = await self.db.execute(
            select(Employee)
            .where(Employee.deleted_at.is_(None), Employee.employment_status == "active")
            .offset(skip)
            .limit(limit)
            .order_by(Employee.employee_id)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Employee:
        emp = Employee(**kwargs)
        self.db.add(emp)
        await self.db.flush()
        await self.db.refresh(emp)
        return emp

    async def update(self, employee_id: int, **kwargs) -> Optional[Employee]:
        await self.db.execute(
            update(Employee).where(Employee.employee_id == employee_id).values(**kwargs)
        )
        return await self.get_by_id(employee_id)

    async def soft_delete(self, employee_id: int) -> None:
        await self.db.execute(
            update(Employee)
            .where(Employee.employee_id == employee_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
