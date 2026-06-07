"""AbsenceRepository — DB access for absences."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.absence import Absence


class AbsenceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> Absence:
        absence = Absence(**kwargs)
        self.db.add(absence)
        await self.db.flush()
        await self.db.refresh(absence)
        return absence

    async def get_by_id(self, absence_id: int) -> Optional[Absence]:
        result = await self.db.execute(
            select(Absence).where(Absence.id == absence_id)
        )
        return result.scalar_one_or_none()

    async def get_by_employee(self, employee_id: int, skip: int = 0, limit: int = 100) -> list[Absence]:
        result = await self.db.execute(
            select(Absence)
            .where(Absence.employee_id == employee_id)
            .order_by(Absence.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_for_manager(self, manager_employee_ids: list[int]) -> list[Absence]:
        """Return pending absences for employees managed by the given manager."""
        if not manager_employee_ids:
            return []
        result = await self.db.execute(
            select(Absence).where(
                Absence.employee_id.in_(manager_employee_ids),
                Absence.status == "pending",
            ).order_by(Absence.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self, employee_ids: list[int], start_date: date, end_date: date
    ) -> list[Absence]:
        if not employee_ids:
            return []
        result = await self.db.execute(
            select(Absence).where(
                Absence.employee_id.in_(employee_ids),
                Absence.status == "approved",
                Absence.start_date <= end_date,
                Absence.end_date >= start_date,
            )
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        absence_id: int,
        status: str,
        approved_by: Optional[int] = None,
        rejection_reason: Optional[str] = None,
    ) -> Optional[Absence]:
        values: dict = {"status": status, "updated_at": datetime.now(timezone.utc)}
        if approved_by is not None:
            values["approved_by"] = approved_by
            values["approved_at"] = datetime.now(timezone.utc)
        if rejection_reason is not None:
            values["rejection_reason"] = rejection_reason
        await self.db.execute(
            update(Absence).where(Absence.id == absence_id).values(**values)
        )
        return await self.get_by_id(absence_id)

    async def get_all(self, status: Optional[str] = None) -> list[Absence]:
        """Return all absences, optionally filtered by status."""
        q = select(Absence).order_by(Absence.created_at.desc())
        if status:
            q = q.where(Absence.status == status)
        result = await self.db.execute(q)
        return list(result.scalars().all())
