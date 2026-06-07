"""OrganizationRepository — DB access for organizations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_active(self) -> list[Organization]:
        result = await self.db.execute(
            select(Organization)
            .where(Organization.deleted_at.is_(None))
            .order_by(Organization.org_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        result = await self.db.execute(
            select(Organization).where(
                Organization.org_id == org_id,
                Organization.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, org_name: str, manager_id: Optional[int] = None) -> Organization:
        org = Organization(org_name=org_name, manager_id=manager_id)
        self.db.add(org)
        await self.db.flush()
        await self.db.refresh(org)
        return org

    async def update(self, org_id: int, **kwargs) -> Optional[Organization]:
        await self.db.execute(
            update(Organization).where(Organization.org_id == org_id).values(**kwargs)
        )
        return await self.get_by_id(org_id)

    async def soft_delete(self, org_id: int) -> None:
        await self.db.execute(
            update(Organization)
            .where(Organization.org_id == org_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )

    async def list_by_manager(self, manager_id: int) -> list[Organization]:
        result = await self.db.execute(
            select(Organization).where(
                Organization.manager_id == manager_id,
                Organization.deleted_at.is_(None),
            ).order_by(Organization.org_id)
        )
        return list(result.scalars().all())

    async def get_employee_count(self, org_id: int) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Employee)
            .where(
                Employee.org_id == org_id,
                Employee.deleted_at.is_(None),
            )
        )
        return result.scalar_one()
