"""EmployeeSuggestionService — suggests available, skilled employees for a project."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.absence import Absence
from app.models.employee import Employee
from app.models.employee_skill import EmployeeSkill
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_required_skill import ProjectRequiredSkill
from app.models.skill_rate import SkillRate
from app.repositories.employee_skill_repository import EmployeeSkillRepository
from app.repositories.project_skill_repository import ProjectSkillRepository
from app.repositories.project_repository import ProjectRepository


class EmployeeSuggestionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.project_skill_repo = ProjectSkillRepository(db)
        self.emp_skill_repo = EmployeeSkillRepository(db)

    async def suggest_employees(self, project_id: int) -> list[dict]:
        """Return ranked list of available, skilled employees for a project.

        Steps:
        1. Load project_required_skills for the project.
        2. Get employees with at least one matching skill.
        3. Filter: no approved absence covering the entire project period.
        4. Filter: no active project overlap (employee in team_members of another
           active project with overlapping dates).
        5. Count matching skills per candidate.
        6. Sort by matching_skill_count descending.
        7. Return list of dicts.
        """
        # 1. Load project and its required skills
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return []

        required_skills = await self.project_skill_repo.list_by_project(project_id)
        if not required_skills:
            return []

        required_skill_ids = [rs.skill_rate_id for rs in required_skills]

        # 2. Get candidate employee IDs (have at least one required skill)
        candidate_ids = await self.emp_skill_repo.get_employees_with_skills(required_skill_ids)
        if not candidate_ids:
            return []

        # Load full employee records with org info in one query
        emp_result = await self.db.execute(
            select(Employee, Organization)
            .join(Organization, Employee.org_id == Organization.org_id)
            .where(
                Employee.employee_id.in_(candidate_ids),
                Employee.deleted_at.is_(None),
                Employee.employment_status == "active",
                Organization.deleted_at.is_(None),
            )
        )
        employees_with_org = emp_result.all()

        if not employees_with_org:
            return []

        active_candidate_ids = [row[0].employee_id for row in employees_with_org]

        # 3. Filter: exclude employees with an approved absence covering the entire project period
        #    Absence covers entire period when: absence.start_date <= project.start_date
        #    AND absence.end_date >= project.end_date
        project_start = project.start_date
        project_end = project.end_date  # may be None

        if project_start and project_end:
            absence_result = await self.db.execute(
                select(Absence.employee_id)
                .where(
                    Absence.employee_id.in_(active_candidate_ids),
                    Absence.status == "approved",
                    Absence.start_date <= project_start,
                    Absence.end_date >= project_end,
                )
                .distinct()
            )
            fully_absent_ids = set(absence_result.scalars().all())
        else:
            fully_absent_ids = set()

        # 4. Filter: exclude employees with an active project overlap
        #    An overlap exists when another active project's date range intersects [project_start, project_end]
        #    and the employee is in that project's team_members (or is the manager).
        if project_start and project_end:
            overlap_result = await self.db.execute(
                select(Project).where(
                    Project.project_id != project_id,
                    Project.deleted_at.is_(None),
                    Project.status == "active",
                    Project.start_date <= project_end,
                    # end_date IS NULL means ongoing — treat as overlapping
                    (Project.end_date.is_(None)) | (Project.end_date >= project_start),
                )
            )
            overlapping_projects = list(overlap_result.scalars().all())
        else:
            overlapping_projects = []

        overlapping_employee_ids: set[int] = set()
        for op in overlapping_projects:
            if op.team_members:
                for mid in op.team_members:
                    overlapping_employee_ids.add(mid)
            # Also exclude the project manager if they are in our candidate pool
            if op.manager_id:
                overlapping_employee_ids.add(op.manager_id)

        # 5. Build per-employee skill map for counting
        # Load all employee skills for candidates in one query
        skill_result = await self.db.execute(
            select(EmployeeSkill, SkillRate)
            .join(SkillRate, EmployeeSkill.skill_rate_id == SkillRate.id)
            .where(EmployeeSkill.employee_id.in_(active_candidate_ids))
        )
        skill_rows = skill_result.all()

        # Map employee_id -> list of (skill_rate_id, skill_name)
        emp_skills: dict[int, list[tuple[int, str]]] = {}
        for es, sr in skill_rows:
            emp_skills.setdefault(es.employee_id, []).append((es.skill_rate_id, sr.skill_name))

        required_skill_id_set = set(required_skill_ids)

        # 6. Build result list
        suggestions = []
        for employee, org in employees_with_org:
            eid = employee.employee_id
            if eid in fully_absent_ids:
                continue
            if eid in overlapping_employee_ids:
                continue

            skills = emp_skills.get(eid, [])
            matching = [
                skill_name
                for skill_rate_id, skill_name in skills
                if skill_rate_id in required_skill_id_set
            ]
            if not matching:
                continue

            suggestions.append({
                "employee_id": eid,
                "full_name": f"{employee.first_name} {employee.last_name}",
                "org_name": org.org_name,
                "matching_skills": matching,
                "matching_skill_count": len(matching),
            })

        # 7. Sort by matching_skill_count descending
        suggestions.sort(key=lambda x: x["matching_skill_count"], reverse=True)
        return suggestions
