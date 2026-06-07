"""SkillRateRepository — DB access for skill rates."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_rate import SkillRate


class SkillRateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_org(self, org_id: int = 1) -> list[SkillRate]:
        result = await self.db.execute(
            select(SkillRate)
            .where(SkillRate.org_id == org_id)
            .order_by(SkillRate.skill_name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, id: int) -> Optional[SkillRate]:
        result = await self.db.execute(select(SkillRate).where(SkillRate.id == id))
        return result.scalar_one_or_none()

    async def create(
        self,
        skill_name: str,
        billing_rate: Decimal,
        org_id: int = 1,
        description: Optional[str] = None,
    ) -> SkillRate:
        sr = SkillRate(
            org_id=org_id,
            skill_name=skill_name,
            billing_rate=billing_rate,
            description=description,
        )
        self.db.add(sr)
        await self.db.flush()
        await self.db.refresh(sr)
        return sr

    async def update(self, id: int, **kwargs) -> Optional[SkillRate]:
        await self.db.execute(
            update(SkillRate).where(SkillRate.id == id).values(**kwargs)
        )
        return await self.get_by_id(id)

    async def delete(self, id: int) -> None:
        await self.db.execute(delete(SkillRate).where(SkillRate.id == id))
