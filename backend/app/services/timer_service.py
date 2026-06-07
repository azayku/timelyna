"""Timer service — start/stop chronometer logic."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timer import ActiveTimer
from app.models.timesheet_entry import TimesheetEntry

logger = logging.getLogger(__name__)


class TimerService:
    """Business logic for timer start/stop."""

    def __init__(self, db: AsyncSession, org_id: int = 1):
        self.db = db
        self.org_id = org_id

    async def start_timer(
        self,
        employee_id: int,
        project_id: int,
        description: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> ActiveTimer:
        """Start a new timer, stopping any existing one first."""
        # Arrêter le timer existant s'il y en a un
        existing = await self.db.execute(
            select(ActiveTimer).where(ActiveTimer.employee_id == employee_id)
        )
        existing_timer = existing.scalar_one_or_none()
        if existing_timer:
            await self.db.delete(existing_timer)
            await self.db.flush()

        timer = ActiveTimer(
            employee_id=employee_id,
            project_id=project_id,
            org_id=self.org_id,
            description=description,
            task_type=task_type,
        )
        self.db.add(timer)
        await self.db.commit()
        await self.db.refresh(timer)
        return timer

    async def get_active_timer(self, employee_id: int) -> Optional[ActiveTimer]:
        """Get the active timer for an employee."""
        result = await self.db.execute(
            select(ActiveTimer).where(ActiveTimer.employee_id == employee_id)
        )
        return result.scalar_one_or_none()

    async def stop_timer(self, employee_id: int) -> dict:
        """Stop the active timer and create a timesheet entry if duration >= 1 minute."""
        timer = await self.get_active_timer(employee_id)
        if not timer:
            return {"stopped": False, "hours_worked": 0.0, "timesheet_entry_id": None}

        now = datetime.now(timezone.utc)
        started_at_utc = timer.started_at
        if started_at_utc.tzinfo is None:
            started_at_utc = started_at_utc.replace(tzinfo=timezone.utc)

        elapsed_seconds = (now - started_at_utc).total_seconds()
        hours_worked = round(elapsed_seconds / 3600, 2)

        # Créer l'entrée timesheet si >= 1 minute
        entry_id = None
        if elapsed_seconds >= 60:
            work_date = timer.started_at.date()
            entry = TimesheetEntry(
                employee_id=employee_id,
                project_id=timer.project_id,
                work_date=work_date,
                hours_worked=Decimal(str(hours_worked)),
                description=timer.description or "Suivi automatique",
                task_type=timer.task_type or "other",
                entry_type="normal",
                billable_flag=True,
                status="draft",
            )
            self.db.add(entry)
            await self.db.flush()
            entry_id = entry.timesheet_entry_id

        await self.db.delete(timer)
        await self.db.commit()

        return {
            "stopped": True,
            "hours_worked": hours_worked,
            "timesheet_entry_id": entry_id,
        }
