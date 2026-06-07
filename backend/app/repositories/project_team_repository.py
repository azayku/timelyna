"""ProjectTeamRepository — DB access for project team members."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_team_member import ProjectTeamMember


class ProjectTeamRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_team(self, project_id: int) -> list[ProjectTeamMember]:
        result = await self.db.execute(
            select(ProjectTeamMember)
            .where(ProjectTeamMember.project_id == project_id)
            .order_by(ProjectTeamMember.assigned_at)
        )
        return list(result.scalars().all())

    async def get_member(self, project_id: int, employee_id: int) -> Optional[ProjectTeamMember]:
        result = await self.db.execute(
            select(ProjectTeamMember).where(
                ProjectTeamMember.project_id == project_id,
                ProjectTeamMember.employee_id == employee_id,
            )
        )
        return result.scalar_one_or_none()

    async def assign_member(
        self,
        project_id: int,
        employee_id: int,
        skill_rate_id: Optional[int] = None,
        custom_rate: Optional[Decimal] = None,
    ) -> ProjectTeamMember:
        # Upsert: update if exists, insert if not
        existing = await self.get_member(project_id, employee_id)
        if existing:
            await self.db.execute(
                update(ProjectTeamMember)
                .where(
                    ProjectTeamMember.project_id == project_id,
                    ProjectTeamMember.employee_id == employee_id,
                )
                .values(skill_rate_id=skill_rate_id, custom_rate=custom_rate)
            )
            await self.db.flush()
            return await self.get_member(project_id, employee_id)  # type: ignore[return-value]

        member = ProjectTeamMember(
            project_id=project_id,
            employee_id=employee_id,
            skill_rate_id=skill_rate_id,
            custom_rate=custom_rate,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_member(self, project_id: int, employee_id: int) -> None:
        await self.db.execute(
            delete(ProjectTeamMember).where(
                ProjectTeamMember.project_id == project_id,
                ProjectTeamMember.employee_id == employee_id,
            )
        )

    async def update_skill(
        self,
        project_id: int,
        employee_id: int,
        skill_rate_id: Optional[int] = None,
        custom_rate: Optional[Decimal] = None,
    ) -> None:
        await self.db.execute(
            update(ProjectTeamMember)
            .where(
                ProjectTeamMember.project_id == project_id,
                ProjectTeamMember.employee_id == employee_id,
            )
            .values(skill_rate_id=skill_rate_id, custom_rate=custom_rate)
        )
