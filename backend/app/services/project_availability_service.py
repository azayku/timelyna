"""ProjectAvailabilityService — team availability for project planning."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.employee_repository import EmployeeRepository
from app.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


def _count_working_days(start: date, end: date) -> int:
    """Count weekdays (Mon–Fri) between start and end inclusive."""
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0=Mon … 4=Fri
            count += 1
        current += timedelta(days=1)
    return count


class ProjectAvailabilityService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_team_availability(
        self, start_date: date, end_date: date
    ) -> list[dict]:
        """Return availability info for all active employees over the period."""
        emp_repo = EmployeeRepository(self.db)
        employees = await emp_repo.list_active(skip=0, limit=500)

        if not employees:
            return []

        # Load org standard hours
        standard_hours = 8.0
        try:
            from app.models.org_settings import OrgSettings
            result = await self.db.execute(
                select(OrgSettings).where(OrgSettings.org_id == 1)
            )
            settings = result.scalar_one_or_none()
            if settings:
                standard_hours = float(settings.standard_hours_per_day)
        except Exception:
            logger.warning("OrgSettings load failed", exc_info=True)

        working_days = _count_working_days(start_date, end_date)
        capacity_hours = working_days * standard_hours

        employee_ids = [e.employee_id for e in employees]
        placeholders = ",".join(str(eid) for eid in employee_ids)

        # Hours logged per employee in the period
        hours_result = await self.db.execute(
            text(f"""
                SELECT employee_id, SUM(hours_worked) AS total_hours
                FROM timesheet_entries
                WHERE employee_id IN ({placeholders})
                  AND work_date BETWEEN :start_date AND :end_date
                  AND deleted_at IS NULL
                GROUP BY employee_id
            """),
            {"start_date": start_date, "end_date": end_date},
        )
        hours_map: dict[int, float] = {
            int(row["employee_id"]): float(row["total_hours"])
            for row in hours_result.mappings().all()
        }

        # Approved absence days per employee
        absence_days_map: dict[int, int] = {}
        try:
            abs_result = await self.db.execute(
                text(f"""
                    SELECT employee_id, start_date, end_date
                    FROM absences
                    WHERE employee_id IN ({placeholders})
                      AND status = 'approved'
                      AND start_date <= :end_date
                      AND end_date >= :start_date
                """),
                {"start_date": start_date, "end_date": end_date},
            )
            for row in abs_result.mappings().all():
                eid = int(row["employee_id"])
                abs_start = row["start_date"]
                abs_end = row["end_date"]
                if isinstance(abs_start, str):
                    abs_start = date.fromisoformat(abs_start)
                if isinstance(abs_end, str):
                    abs_end = date.fromisoformat(abs_end)
                # Clamp to period
                clamped_start = max(abs_start, start_date)
                clamped_end = min(abs_end, end_date)
                days = _count_working_days(clamped_start, clamped_end)
                absence_days_map[eid] = absence_days_map.get(eid, 0) + days
        except Exception:
            logger.warning("Absence days load failed", exc_info=True)

        # Active projects per employee in the period (conflicts)
        conflicts_map: dict[int, list[str]] = {}
        try:
            proj_result = await self.db.execute(
                text(f"""
                    SELECT DISTINCT te.employee_id, p.project_name
                    FROM timesheet_entries te
                    JOIN projects p ON p.project_id = te.project_id
                    WHERE te.employee_id IN ({placeholders})
                      AND te.work_date BETWEEN :start_date AND :end_date
                      AND te.deleted_at IS NULL
                      AND p.status = 'active'
                """),
                {"start_date": start_date, "end_date": end_date},
            )
            for row in proj_result.mappings().all():
                eid = int(row["employee_id"])
                conflicts_map.setdefault(eid, []).append(row["project_name"])
        except Exception:
            logger.warning("Project conflicts load failed", exc_info=True)

        result_list = []
        for emp in employees:
            eid = emp.employee_id
            hours_logged = hours_map.get(eid, 0.0)
            occupation_pct = (
                round(hours_logged / capacity_hours * 100, 1)
                if capacity_hours > 0
                else 0.0
            )
            result_list.append({
                "employee_id": eid,
                "full_name": f"{emp.first_name} {emp.last_name}",
                "occupation_pct": occupation_pct,
                "hours_logged": hours_logged,
                "capacity_hours": capacity_hours,
                "absence_days": absence_days_map.get(eid, 0),
                "conflicts": conflicts_map.get(eid, []),
                "warning": occupation_pct > 80,
            })

        return result_list
