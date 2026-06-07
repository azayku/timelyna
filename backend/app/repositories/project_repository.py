"""ProjectRepository — DB access for projects."""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.client import Client


class ProjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, project_id: int) -> Optional[Project]:
        result = await self.db.execute(
            select(Project).where(
                Project.project_id == project_id,
                Project.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Project]:
        result = await self.db.execute(
            select(Project).where(
                Project.project_code == code,
                Project.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_active_for_employee(
        self, employee_id: int, reference_date: date | None = None
    ) -> list[dict]:
        """Return active projects where employee is manager or in team_members.

        If reference_date is provided, only return projects whose date range
        includes that date: start_date <= reference_date AND (end_date IS NULL
        OR end_date >= reference_date).
        
        Returns projects with client information (name and address).
        """
        conditions = [
            Project.deleted_at.is_(None),
            Project.status == "active",
        ]
        if reference_date is not None:
            conditions.append(Project.start_date <= reference_date)
            conditions.append(
                or_(Project.end_date.is_(None), Project.end_date >= reference_date)
            )

        # Join with Client table to get client info
        result = await self.db.execute(
            select(Project, Client.client_name, Client.address)
            .join(Client, Project.client_id == Client.client_id)
            .where(*conditions)
        )
        rows = result.all()
        
        # Filter in Python since JSON array membership is DB-specific
        filtered = []
        for project, client_name, client_address in rows:
            if project.manager_id == employee_id or (project.team_members and employee_id in project.team_members):
                # Create a dict with project attributes + client info
                project_dict = {
                    "project_id": project.project_id,
                    "client_id": project.client_id,
                    "project_name": project.project_name,
                    "project_code": project.project_code,
                    "description": project.description,
                    "status": project.status,
                    "start_date": project.start_date,
                    "end_date": project.end_date,
                    "budget_hours": project.budget_hours,
                    "budget_alert_threshold": project.budget_alert_threshold,
                    "budget_amount": project.budget_amount,
                    "billing_rate": project.billing_rate,
                    "manager_id": project.manager_id,
                    "team_members": project.team_members,
                    "client_name": client_name,
                    "client_address": client_address,
                }
                filtered.append(project_dict)
        
        return filtered

    async def list_all_active(self, skip: int = 0, limit: int = 100) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.deleted_at.is_(None), Project.status == "active")
            .offset(skip)
            .limit(limit)
            .order_by(Project.project_id)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Project:
        project = Project(**kwargs)
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project_id: int, **kwargs) -> Optional[Project]:
        await self.db.execute(
            update(Project).where(Project.project_id == project_id).values(**kwargs)
        )
        return await self.get_by_id(project_id)

    async def deactivate(self, project_id: int) -> None:
        await self.db.execute(
            update(Project)
            .where(Project.project_id == project_id)
            .values(status="inactive")
        )

    async def deactivate_by_client(self, client_id: int) -> None:
        await self.db.execute(
            update(Project)
            .where(Project.client_id == client_id, Project.status == "active")
            .values(status="inactive")
        )
