"""EmployeeSkillRepository — DB access for employee skills."""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_skill import EmployeeSkill
from app.models.skill_rate import SkillRate


class EmployeeSkillRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_employee(self, employee_id: int) -> list[EmployeeSkill]:
        result = await self.db.execute(
            select(EmployeeSkill)
            .join(SkillRate, EmployeeSkill.skill_rate_id == SkillRate.id)
            .where(EmployeeSkill.employee_id == employee_id)
            .order_by(SkillRate.skill_name)
        )
        return list(result.scalars().all())

    async def add(self, employee_id: int, skill_rate_id: int) -> EmployeeSkill:
        skill = EmployeeSkill(employee_id=employee_id, skill_rate_id=skill_rate_id)
        self.db.add(skill)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Employee already has this skill")
        await self.db.refresh(skill)
        return skill

    async def remove(self, employee_id: int, skill_rate_id: int) -> None:
        await self.db.execute(
            delete(EmployeeSkill).where(
                EmployeeSkill.employee_id == employee_id,
                EmployeeSkill.skill_rate_id == skill_rate_id,
            )
        )

    async def get_employees_with_skills(self, skill_rate_ids: list[int]) -> list[int]:
        if not skill_rate_ids:
            return []
        result = await self.db.execute(
            select(EmployeeSkill.employee_id)
            .where(EmployeeSkill.skill_rate_id.in_(skill_rate_ids))
            .distinct()
        )
        return list(result.scalars().all())
