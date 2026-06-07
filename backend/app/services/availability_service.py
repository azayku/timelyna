"""AvailabilityService — business logic for employee availability view."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.project_repository import ProjectRepository


class AvailabilityService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.avail_repo = AvailabilityRepository(db)
        self.emp_repo = EmployeeRepository(db)
        self.proj_repo = ProjectRepository(db)

    async def get_availability(
        self,
        start_date: date,
        end_date: date,
        department: str | None = None,
        project_id: int | None = None,
    ) -> dict:
        # 1. Load active employees
        employees = await self.emp_repo.list_active(skip=0, limit=500)

        # 2. Filter by department
        if department:
            employees = [e for e in employees if e.department == department]

        # 3. Filter by project team members
        if project_id is not None:
            project = await self.proj_repo.get_by_id(project_id)
            if project and project.team_members:
                team_ids = set(project.team_members)
                employees = [e for e in employees if e.employee_id in team_ids]
            else:
                employees = []

        employee_ids = [e.employee_id for e in employees]

        # 4. Load hours and absences
        hours_map = await self.avail_repo.get_hours_by_employee_and_date(
            employee_ids, start_date, end_date
        )
        absences_map = await self.avail_repo.get_absences_by_employee_and_date(
            employee_ids, start_date, end_date
        )

        # 5. Load OrgSettings for standard_hours_per_day
        standard_hours = 8.0
        try:
            from app.models.org_settings import OrgSettings
            from sqlalchemy import select
            result = await self.db.execute(select(OrgSettings).where(OrgSettings.org_id == 1))
            settings = result.scalar_one_or_none()
            if settings:
                standard_hours = float(settings.standard_hours_per_day)
        except Exception:
            pass

        # 6. Build date list (weekdays only)
        dates: list[str] = []
        current = start_date
        while current <= end_date:
            dates.append(str(current))
            current += timedelta(days=1)

        # 7. Build employee availability data
        employees_data = []
        for emp in employees:
            days: dict[str, dict] = {}
            for d_str in dates:
                d = date.fromisoformat(d_str)
                hours_logged = hours_map.get((emp.employee_id, d), 0.0)
                absence = absences_map.get((emp.employee_id, d))
                occupation_pct = (hours_logged / standard_hours * 100) if standard_hours > 0 else 0.0
                days[d_str] = {
                    "hours_logged": hours_logged,
                    "occupation_pct": round(occupation_pct, 1),
                    "absence": absence,
                }
            employees_data.append({
                "employee_id": emp.employee_id,
                "full_name": f"{emp.first_name} {emp.last_name}",
                "department": emp.department,
                "days": days,
            })

        return {
            "dates": dates,
            "standard_hours_per_day": standard_hours,
            "employees": employees_data,
        }
