"""TimesheetRepository — DB access for timesheet entries and approvals."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval
from app.models.timesheet_entry import TimesheetEntry


class TimesheetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_week(
        self, employee_id: int, start_date: date, end_date: date
    ) -> list[TimesheetEntry]:
        result = await self.db.execute(
            select(TimesheetEntry).where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.work_date >= start_date,
                TimesheetEntry.work_date <= end_date,
                TimesheetEntry.deleted_at.is_(None),
            ).order_by(TimesheetEntry.work_date)
        )
        return list(result.scalars().all())

    async def get_by_id(self, entry_id: int) -> Optional[TimesheetEntry]:
        result = await self.db.execute(
            select(TimesheetEntry).where(
                TimesheetEntry.timesheet_entry_id == entry_id,
                TimesheetEntry.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> TimesheetEntry:
        entry = TimesheetEntry(**kwargs)
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def update(self, entry_id: int, **kwargs) -> Optional[TimesheetEntry]:
        await self.db.execute(
            update(TimesheetEntry)
            .where(TimesheetEntry.timesheet_entry_id == entry_id)
            .values(**kwargs)
        )
        return await self.get_by_id(entry_id)

    async def soft_delete(self, entry_id: int) -> None:
        await self.db.execute(
            update(TimesheetEntry)
            .where(TimesheetEntry.timesheet_entry_id == entry_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )

    async def get_daily_total(self, employee_id: int, work_date: date) -> Decimal:
        result = await self.db.execute(
            select(func.coalesce(func.sum(TimesheetEntry.hours_worked), 0)).where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.work_date == work_date,
                TimesheetEntry.deleted_at.is_(None),
            )
        )
        return result.scalar_one() or Decimal("0")

    async def get_week_draft_entries(
        self, employee_id: int, start_date: date, end_date: date
    ) -> list[TimesheetEntry]:
        result = await self.db.execute(
            select(TimesheetEntry).where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.work_date >= start_date,
                TimesheetEntry.work_date <= end_date,
                TimesheetEntry.status.in_(["draft", "rejected"]),
                TimesheetEntry.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def get_approval_for_week(
        self, employee_id: int, week_start: date
    ) -> Optional[Approval]:
        result = await self.db.execute(
            select(Approval).where(
                Approval.employee_id == employee_id,
                Approval.week_start == week_start,
            )
        )
        return result.scalar_one_or_none()

    async def create_approval(
        self, employee_id: int, manager_id: Optional[int], week_start: date
    ) -> Approval:
        approval = Approval(
            employee_id=employee_id,
            manager_id=manager_id,
            week_start=week_start,
            status="pending",
        )
        self.db.add(approval)
        await self.db.flush()
        await self.db.refresh(approval)
        return approval

    async def update_status(self, approval_id: int, status: str) -> None:
        await self.db.execute(
            update(Approval)
            .where(Approval.approval_id == approval_id)
            .values(status=status, decided_at=None, rejection_reason=None)
        )
        await self.db.flush()

    async def submit_week_entries(
        self, employee_id: int, start_date: date, end_date: date
    ) -> None:
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(TimesheetEntry)
            .where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.work_date >= start_date,
                TimesheetEntry.work_date <= end_date,
                TimesheetEntry.status.in_(["draft", "rejected"]),
                TimesheetEntry.deleted_at.is_(None),
            )
            .values(status="submitted", submitted_at=now)
        )
