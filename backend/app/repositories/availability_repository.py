"""AvailabilityRepository — DB access for availability calculations."""
from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AvailabilityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_hours_by_employee_and_date(
        self, employee_ids: list[int], start_date: date, end_date: date
    ) -> dict[tuple[int, date], float]:
        """Return {(employee_id, work_date): total_hours}."""
        if not employee_ids:
            return {}

        placeholders = ",".join(str(eid) for eid in employee_ids)
        result = await self.db.execute(
            text(f"""
                SELECT employee_id, work_date, SUM(hours_worked) AS total_hours
                FROM timesheet_entries
                WHERE employee_id IN ({placeholders})
                  AND work_date BETWEEN :start_date AND :end_date
                  AND deleted_at IS NULL
                GROUP BY employee_id, work_date
            """),
            {"start_date": start_date, "end_date": end_date},
        )
        out: dict[tuple[int, date], float] = {}
        for row in result.mappings().all():
            key = (int(row["employee_id"]), row["work_date"])
            out[key] = float(row["total_hours"])
        return out

    async def get_absences_by_employee_and_date(
        self, employee_ids: list[int], start_date: date, end_date: date
    ) -> dict[tuple[int, date], dict]:
        """Return {(employee_id, date): {"type": ..., "status": ...}} for approved absences."""
        if not employee_ids:
            return {}

        out: dict[tuple[int, date], dict] = {}
        try:
            placeholders = ",".join(str(eid) for eid in employee_ids)
            result = await self.db.execute(
                text(f"""
                    SELECT employee_id, absence_type, start_date, end_date, status
                    FROM absences
                    WHERE employee_id IN ({placeholders})
                      AND status = 'approved'
                      AND start_date <= :end_date
                      AND end_date >= :start_date
                """),
                {"start_date": start_date, "end_date": end_date},
            )
            from datetime import timedelta
            for row in result.mappings().all():
                # Expand each absence across its date range
                current = row["start_date"]
                if isinstance(current, str):
                    from datetime import date as _date
                    current = _date.fromisoformat(current)
                abs_end = row["end_date"]
                if isinstance(abs_end, str):
                    from datetime import date as _date
                    abs_end = _date.fromisoformat(abs_end)
                while current <= abs_end:
                    if start_date <= current <= end_date:
                        key = (int(row["employee_id"]), current)
                        out[key] = {"type": row["absence_type"], "status": row["status"]}
                    current += timedelta(days=1)
        except Exception:
            # absences table may not exist yet
            pass
        return out
