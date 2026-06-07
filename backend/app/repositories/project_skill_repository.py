"""ProjectSkillRepository — DB access for project required skills."""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_required_skill import ProjectRequiredSkill


class ProjectSkillRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_project(self, project_id: int) -> list[ProjectRequiredSkill]:
        result = await self.db.execute(
            select(ProjectRequiredSkill)
            .where(ProjectRequiredSkill.project_id == project_id)
            .order_by(ProjectRequiredSkill.id)
        )
        return list(result.scalars().all())

    async def set_skills(self, project_id: int, skills: list[dict]) -> list[ProjectRequiredSkill]:
        await self.delete_by_project(project_id)
        created: list[ProjectRequiredSkill] = []
        for skill in skills:
            row = ProjectRequiredSkill(
                project_id=project_id,
                skill_rate_id=skill["skill_rate_id"],
                quantity=skill.get("quantity", 1),
            )
            self.db.add(row)
            created.append(row)
        await self.db.flush()
        for row in created:
            await self.db.refresh(row)
        return created

    async def delete_by_project(self, project_id: int) -> None:
        await self.db.execute(
            delete(ProjectRequiredSkill).where(
                ProjectRequiredSkill.project_id == project_id
            )
        )
