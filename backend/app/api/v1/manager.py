"""Manager-specific routes — /api/v1/manager/..."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.module_license_deps import require_module_license
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.employee_skill import EmployeeSkill
from app.models.skill_rate import SkillRate
from app.models.approval import Approval
from app.models.timesheet_entry import TimesheetEntry
from app.models.project import Project
from app.models.client import Client
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/manager", tags=["manager"])

_manager_or_admin = require_role("manager", "admin")
_require_advanced_approvals = require_module_license("advanced_approvals")


class ManagerProjectResponse(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    client_name: str
    client_address: str | None
    status: str
    start_date: str
    end_date: str | None
    budget_hours: float | None
    hours_consumed: float
    budget_percent: float | None  # % of budget_hours consumed


class OrganizationResponse(BaseModel):
    organization_id: int
    organization_name: str
    employee_count: int
    manager_name: str
    created_at: str

    class Config:
        from_attributes = True
        # Permet de mapper org_id -> organization_id et org_name -> organization_name
        populate_by_name = True
        
    @classmethod
    def from_orm_with_details(cls, org: Organization, count: int, manager_name: str):
        """Create response from ORM object with employee count and manager name."""
        return cls(
            organization_id=org.org_id,
            organization_name=org.org_name,
            employee_count=count,
            manager_name=manager_name,
            created_at=org.created_at.isoformat() if org.created_at else ""
        )


class TeamMemberResponse(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    email: str
    hire_date: str | None
    organization_name: str
    skills: list[str]  # Liste des noms de compétences

    class Config:
        from_attributes = True


@router.get("/organizations", response_model=List[OrganizationResponse])
async def get_manager_organizations(
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all organizations where the current user is the manager.
    Returns organization details with employee count.
    """
    import logging
    logger = logging.getLogger("app.manager")
    
    employee_id = current_user["employee_id"]
    logger.info(f"[MANAGER] Getting organizations for user_id={employee_id}, email={current_user.get('sub')}")
    
    # Get organizations where current user is manager
    stmt = (
        select(Organization)
        .where(Organization.manager_id == employee_id)
        .where(Organization.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    organizations = result.scalars().all()
    
    logger.info(f"[MANAGER] Found {len(organizations)} organizations")

    # Count employees for each organization
    response = []
    for org in organizations:
        logger.info(f"[MANAGER] Processing org_id={org.org_id}, org_name={org.org_name}")
        
        # Count employees
        count_stmt = (
            select(func.count(Employee.employee_id))
            .where(Employee.org_id == org.org_id)
            .where(Employee.deleted_at.is_(None))
            .where(Employee.employment_status == "active")
        )
        count_result = await db.execute(count_stmt)
        employee_count = count_result.scalar() or 0
        logger.info(f"[MANAGER] org_id={org.org_id} has {employee_count} active employees")
        
        # Get manager name
        manager_stmt = (
            select(Employee.first_name, Employee.last_name)
            .where(Employee.employee_id == org.manager_id)
        )
        manager_result = await db.execute(manager_stmt)
        manager_row = manager_result.first()
        manager_name = f"{manager_row[0]} {manager_row[1]}" if manager_row else "Non assigné"

        response.append(
            OrganizationResponse.from_orm_with_details(org, employee_count, manager_name)
        )

    logger.info(f"[MANAGER] Returning {len(response)} organizations")
    return response


@router.get("/team", response_model=List[TeamMemberResponse])
async def get_manager_team(
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all team members (employees) in organizations managed by the current user.
    Returns employee details with organization name.
    """
    import logging
    logger = logging.getLogger("app.manager")
    
    employee_id = current_user["employee_id"]
    logger.info(f"[MANAGER] Getting team for user_id={employee_id}, email={current_user.get('sub')}")
    
    # Get all organizations where current user is manager
    org_stmt = (
        select(Organization.org_id)
        .where(Organization.manager_id == employee_id)
        .where(Organization.deleted_at.is_(None))
    )
    org_result = await db.execute(org_stmt)
    org_rows = org_result.all()
    org_ids = [row[0] for row in org_rows]
    
    logger.info(f"[MANAGER] Found {len(org_ids)} organizations: {org_ids}")

    if not org_ids:
        logger.info("[MANAGER] No organizations found, returning empty list")
        return []

    # Get all employees in these organizations
    stmt = (
        select(Employee, Organization.org_name)
        .join(Organization, Employee.org_id == Organization.org_id)
        .where(Employee.org_id.in_(org_ids))
        .where(Employee.deleted_at.is_(None))
        .where(Employee.employment_status == "active")
        .order_by(Employee.last_name, Employee.first_name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for employee, org_name in rows:
        # Get employee skills
        skills_stmt = (
            select(SkillRate.skill_name)
            .join(EmployeeSkill, EmployeeSkill.skill_rate_id == SkillRate.id)
            .where(EmployeeSkill.employee_id == employee.employee_id)
            .order_by(SkillRate.skill_name)
        )
        skills_result = await db.execute(skills_stmt)
        skills = [row[0] for row in skills_result.all()]
        
        response.append(
            TeamMemberResponse(
                employee_id=employee.employee_id,
                first_name=employee.first_name or "",
                last_name=employee.last_name or "",
                email=employee.email,
                hire_date=employee.hire_date.isoformat() if employee.hire_date else None,
                organization_name=org_name,
                skills=skills,
            )
        )

    return response


# ─── Manager Projects Route ───────────────────────────────────────────────

@router.get("/projects", response_model=List[ManagerProjectResponse])
async def get_manager_projects(
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all projects managed by the current user, with client info and budget consumption.
    """
    manager_id = current_user["employee_id"]

    stmt = (
        select(Project, Client.client_name, Client.address)
        .join(Client, Project.client_id == Client.client_id)
        .where(Project.manager_id == manager_id)
        .where(Project.deleted_at.is_(None))
        .where(Client.deleted_at.is_(None))
        .order_by(Project.start_date.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for project, client_name, client_address in rows:
        # Sum all approved/submitted hours for this project
        hours_stmt = select(func.sum(TimesheetEntry.hours_worked)).where(
            TimesheetEntry.project_id == project.project_id,
            TimesheetEntry.deleted_at.is_(None),
            TimesheetEntry.status.in_(["approved", "submitted"]),
        )
        hours_result = await db.execute(hours_stmt)
        hours_consumed = float(hours_result.scalar() or 0)

        budget_hours = float(project.budget_hours) if project.budget_hours else None
        budget_percent = round((hours_consumed / budget_hours) * 100, 1) if budget_hours else None

        response.append(
            ManagerProjectResponse(
                project_id=project.project_id,
                project_name=project.project_name,
                project_code=project.project_code,
                client_name=client_name,
                client_address=client_address,
                status=project.status,
                start_date=project.start_date.isoformat(),
                end_date=project.end_date.isoformat() if project.end_date else None,
                budget_hours=budget_hours,
                hours_consumed=hours_consumed,
                budget_percent=budget_percent,
            )
        )

    return response


# ─── Project Detail Route ──────────────────────────────────────────────────

class ProjectTeamMember(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    email: str
    skills: list[str]


class ProjectDetailResponse(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    description: str | None
    client_name: str
    client_address: str | None
    status: str
    start_date: str
    end_date: str | None
    budget_hours: float | None
    budget_amount: float | None
    hours_consumed: float
    budget_percent: float | None
    team_members: list[ProjectTeamMember]


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_manager_project_detail(
    project_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single project detail with resolved team members."""
    manager_id = current_user["employee_id"]

    stmt = (
        select(Project, Client.client_name, Client.address)
        .join(Client, Project.client_id == Client.client_id)
        .where(Project.project_id == project_id)
        .where(Project.manager_id == manager_id)
        .where(Project.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    project, client_name, client_address = row

    # Hours consumed
    hours_result = await db.execute(
        select(func.sum(TimesheetEntry.hours_worked)).where(
            TimesheetEntry.project_id == project.project_id,
            TimesheetEntry.deleted_at.is_(None),
            TimesheetEntry.status.in_(["approved", "submitted"]),
        )
    )
    hours_consumed = float(hours_result.scalar() or 0)
    budget_hours = float(project.budget_hours) if project.budget_hours else None
    budget_amount = float(project.budget_amount) if project.budget_amount else None
    budget_percent = round((hours_consumed / budget_hours) * 100, 1) if budget_hours else None

    # Resolve team members: distinct employees who have logged time on this project
    emp_ids_stmt = (
        select(TimesheetEntry.employee_id)
        .where(
            TimesheetEntry.project_id == project.project_id,
            TimesheetEntry.deleted_at.is_(None),
        )
        .distinct()
    )
    emp_ids_result = await db.execute(emp_ids_stmt)
    team_member_ids = [row[0] for row in emp_ids_result.all()]

    team_members_out: list[ProjectTeamMember] = []
    if team_member_ids:
        emp_stmt = (
            select(Employee)
            .where(Employee.employee_id.in_(team_member_ids))
            .where(Employee.deleted_at.is_(None))
            .order_by(Employee.last_name, Employee.first_name)
        )
        emp_result = await db.execute(emp_stmt)
        employees = emp_result.scalars().all()

        for emp in employees:
            skills_result = await db.execute(
                select(SkillRate.skill_name)
                .join(EmployeeSkill, EmployeeSkill.skill_rate_id == SkillRate.id)
                .where(EmployeeSkill.employee_id == emp.employee_id)
                .order_by(SkillRate.skill_name)
            )
            skills = [r[0] for r in skills_result.all()]
            team_members_out.append(ProjectTeamMember(
                employee_id=emp.employee_id,
                first_name=emp.first_name or "",
                last_name=emp.last_name or "",
                email=emp.email,
                skills=skills,
            ))

    return ProjectDetailResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        project_code=project.project_code,
        description=project.description,
        client_name=client_name,
        client_address=client_address,
        status=project.status,
        start_date=project.start_date.isoformat(),
        end_date=project.end_date.isoformat() if project.end_date else None,
        budget_hours=budget_hours,
        budget_amount=budget_amount,
        hours_consumed=hours_consumed,
        budget_percent=budget_percent,
        team_members=team_members_out,
    )


# ─── Manager Employee Skill Routes ────────────────────────────────────────

class SkillRateItem(BaseModel):
    id: int
    skill_name: str

class EmployeeSkillDetail(BaseModel):
    id: int
    skill_rate_id: int
    skill_name: str

class AddSkillRequest(BaseModel):
    skill_rate_id: int


async def _assert_team_employee(manager_id: int, employee_id: int, db: AsyncSession) -> Employee:
    """Raise 403 if employee does not belong to one of the manager's organizations."""
    org_ids_result = await db.execute(
        select(Organization.org_id)
        .where(Organization.manager_id == manager_id)
        .where(Organization.deleted_at.is_(None))
    )
    org_ids = [r[0] for r in org_ids_result.all()]
    if not org_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    emp_result = await db.execute(
        select(Employee)
        .where(Employee.employee_id == employee_id)
        .where(Employee.org_id.in_(org_ids))
        .where(Employee.deleted_at.is_(None))
    )
    employee = emp_result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=403, detail="Employee not in your team")
    return employee


@router.get("/skill-rates", response_model=list[SkillRateItem])
async def get_available_skill_rates(
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all skill rates available in the manager's organization."""
    manager_id = current_user["employee_id"]
    # Get manager's own org_id from Employee record
    emp_result = await db.execute(
        select(Employee.org_id).where(Employee.employee_id == manager_id)
    )
    row = emp_result.first()
    if not row:
        return []
    org_id = row[0]
    rates_result = await db.execute(
        select(SkillRate.id, SkillRate.skill_name)
        .where(SkillRate.org_id == org_id)
        .order_by(SkillRate.skill_name)
    )
    return [SkillRateItem(id=r[0], skill_name=r[1]) for r in rates_result.all()]


@router.get("/employees/{employee_id}/skills", response_model=list[EmployeeSkillDetail])
async def get_employee_skills(
    employee_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List skills of a team member."""
    manager_id = current_user["employee_id"]
    await _assert_team_employee(manager_id, employee_id, db)
    result = await db.execute(
        select(EmployeeSkill.id, EmployeeSkill.skill_rate_id, SkillRate.skill_name)
        .join(SkillRate, SkillRate.id == EmployeeSkill.skill_rate_id)
        .where(EmployeeSkill.employee_id == employee_id)
        .order_by(SkillRate.skill_name)
    )
    return [EmployeeSkillDetail(id=r[0], skill_rate_id=r[1], skill_name=r[2]) for r in result.all()]


@router.post("/employees/{employee_id}/skills", response_model=EmployeeSkillDetail, status_code=201)
async def add_employee_skill_manager(
    employee_id: int,
    body: AddSkillRequest,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a skill to a team member."""
    manager_id = current_user["employee_id"]
    await _assert_team_employee(manager_id, employee_id, db)
    # Check not already assigned
    existing = await db.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.skill_rate_id == body.skill_rate_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Skill already assigned")
    skill_name_result = await db.execute(
        select(SkillRate.skill_name).where(SkillRate.id == body.skill_rate_id)
    )
    skill_name_row = skill_name_result.first()
    if not skill_name_row:
        raise HTTPException(status_code=404, detail="Skill rate not found")
    new_skill = EmployeeSkill(employee_id=employee_id, skill_rate_id=body.skill_rate_id)
    db.add(new_skill)
    await db.commit()
    await db.refresh(new_skill)
    return EmployeeSkillDetail(id=new_skill.id, skill_rate_id=new_skill.skill_rate_id, skill_name=skill_name_row[0])


@router.delete("/employees/{employee_id}/skills/{skill_rate_id}", status_code=204)
async def remove_employee_skill_manager(
    employee_id: int,
    skill_rate_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill from a team member."""
    manager_id = current_user["employee_id"]
    await _assert_team_employee(manager_id, employee_id, db)
    result = await db.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.skill_rate_id == skill_rate_id,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not assigned")
    await db.delete(skill)
    await db.commit()


# ─── Approval Schemas ──────────────────────────────────────────────────────

class ApproveRequest(BaseModel):
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    rejection_reason: str


class ApprovalResponse(BaseModel):
    approval_id: int
    employee_id: int
    employee_name: str
    organization_name: str
    week_start: str
    total_hours: float
    status: str
    submitted_at: str | None
    decided_at: str | None
    updated_at: str | None
    rejection_reason: str | None
    notes: str | None


# ─── Manager Approval Routes ──────────────────────────────────────────────

@router.get("/approvals", response_model=List[ApprovalResponse])
async def get_manager_approvals(
    status: str = Query("pending"),
    year: Optional[int] = Query(None),
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all approvals for employees in organizations managed by the current user.
    Filters: status (pending/approved/rejected/all), year
    """
    import logging
    logger = logging.getLogger("app.manager")
    
    employee_id = current_user["employee_id"]
    logger.info(f"[MANAGER APPROVALS] Getting approvals for manager_id={employee_id}, status={status}, year={year}")
    
    # Get all organizations where current user is manager
    org_stmt = (
        select(Organization.org_id)
        .where(Organization.manager_id == employee_id)
        .where(Organization.deleted_at.is_(None))
    )
    org_result = await db.execute(org_stmt)
    org_ids = [row[0] for row in org_result.all()]
    
    if not org_ids:
        return []

    # Build query for approvals
    stmt = (
        select(
            Approval,
            Employee.first_name,
            Employee.last_name,
            Organization.org_name,
        )
        .join(Employee, Approval.employee_id == Employee.employee_id)
        .join(Organization, Employee.org_id == Organization.org_id)
        .where(Employee.org_id.in_(org_ids))
        .where(Employee.deleted_at.is_(None))
    )
    
    # Filter by status
    if status != "all":
        stmt = stmt.where(Approval.status == status)
    
    # Filter by year
    if year:
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        stmt = stmt.where(Approval.week_start >= start_date, Approval.week_start <= end_date)
    
    stmt = stmt.order_by(Approval.week_start.desc(), Employee.last_name)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    response = []
    for approval, first_name, last_name, org_name in rows:
        # Calculate total hours for this approval
        week_end = approval.week_start + timedelta(days=6)
        hours_stmt = (
            select(func.sum(TimesheetEntry.hours_worked))
            .where(
                TimesheetEntry.employee_id == approval.employee_id,
                TimesheetEntry.work_date >= approval.week_start,
                TimesheetEntry.work_date <= week_end,
                TimesheetEntry.deleted_at.is_(None),
            )
        )
        hours_result = await db.execute(hours_stmt)
        total_hours = float(hours_result.scalar() or 0)
        
        response.append(
            ApprovalResponse(
                approval_id=approval.approval_id,
                employee_id=approval.employee_id,
                employee_name=f"{first_name} {last_name}",
                organization_name=org_name,
                week_start=approval.week_start.isoformat(),
                total_hours=total_hours,
                status=approval.status,
                submitted_at=approval.created_at.isoformat() if approval.created_at else None,
                decided_at=approval.decided_at.isoformat() if approval.decided_at else None,
                updated_at=approval.updated_at.isoformat() if approval.updated_at else None,
                rejection_reason=approval.rejection_reason,
                notes=approval.notes,
            )
        )
    
    logger.info(f"[MANAGER APPROVALS] Returning {len(response)} approvals")
    return response


@router.get("/approvals/{approval_id}/entries")
async def get_approval_entries(
    approval_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all timesheet entries for a specific approval."""
    # Get approval
    approval_stmt = select(Approval).where(Approval.approval_id == approval_id)
    approval_result = await db.execute(approval_stmt)
    approval = approval_result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Verify manager has access (via organization)
    employee_stmt = (
        select(Employee.org_id)
        .where(Employee.employee_id == approval.employee_id)
    )
    employee_result = await db.execute(employee_stmt)
    employee_org_id = employee_result.scalar_one_or_none()
    
    org_stmt = (
        select(Organization.manager_id)
        .where(Organization.org_id == employee_org_id)
    )
    org_result = await db.execute(org_stmt)
    manager_id = org_result.scalar_one_or_none()
    
    if manager_id != current_user["employee_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this approval")
    
    # Get entries with client name
    week_end = approval.week_start + timedelta(days=6)
    entries_stmt = (
        select(TimesheetEntry, Project.project_name, Client.client_name)
        .join(Project, Project.project_id == TimesheetEntry.project_id)
        .join(Client, Client.client_id == Project.client_id)
        .where(
            TimesheetEntry.employee_id == approval.employee_id,
            TimesheetEntry.work_date >= approval.week_start,
            TimesheetEntry.work_date <= week_end,
            TimesheetEntry.deleted_at.is_(None),
        )
        .order_by(TimesheetEntry.work_date, Project.project_name)
    )
    entries_result = await db.execute(entries_stmt)
    rows = entries_result.all()
    
    return [
        {
            "timesheet_entry_id": entry.timesheet_entry_id,
            "work_date": entry.work_date.isoformat(),
            "project_name": project_name,
            "client_name": client_name,
            "entry_type": entry.entry_type,
            "hours_worked": float(entry.hours_worked),
            "description": entry.description,
            "notes": entry.notes,
            "billable_flag": entry.billable_flag,
            "status": entry.status,
            "approved_at": entry.approved_at.isoformat() if entry.approved_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }
        for entry, project_name, client_name in rows
    ]


@router.post("/approvals/{approval_id}/approve")
async def approve_approval(
    approval_id: int,
    body: ApproveRequest,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve a timesheet submission."""
    svc = ApprovalService(db)
    return await svc.approve(
        current_user["employee_id"],
        approval_id,
        notes=body.notes,
        is_admin=(current_user["role"] == "admin"),
    )


@router.post("/approvals/{approval_id}/reject")
async def reject_approval(
    approval_id: int,
    body: RejectRequest,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject a timesheet submission."""
    svc = ApprovalService(db)
    return await svc.reject(
        current_user["employee_id"],
        approval_id,
        rejection_reason=body.rejection_reason,
        is_admin=(current_user["role"] == "admin"),
    )


@router.post("/approvals/{approval_id}/entries/{entry_id}/approve")
async def approve_entry(
    approval_id: int,
    entry_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
    _license: None = Depends(_require_advanced_approvals),
):
    """Approve a single timesheet entry. Requires advanced_approvals license."""
    # Verify manager has access to this approval
    approval_stmt = select(Approval).where(Approval.approval_id == approval_id)
    approval_result = await db.execute(approval_stmt)
    approval = approval_result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Verify manager has access via organization
    employee_stmt = select(Employee.org_id).where(Employee.employee_id == approval.employee_id)
    employee_result = await db.execute(employee_stmt)
    employee_org_id = employee_result.scalar_one_or_none()
    
    org_stmt = select(Organization.manager_id).where(Organization.org_id == employee_org_id)
    org_result = await db.execute(org_stmt)
    manager_id = org_result.scalar_one_or_none()
    
    if manager_id != current_user["employee_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update entry status
    entry_stmt = (
        select(TimesheetEntry)
        .where(
            TimesheetEntry.timesheet_entry_id == entry_id,
            TimesheetEntry.employee_id == approval.employee_id,
        )
    )
    entry_result = await db.execute(entry_stmt)
    entry = entry_result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.status = "approved"
    entry.approved_at = datetime.utcnow()
    entry.notes = None
    await db.commit()
    
    return {"message": "Entry approved", "entry_id": entry_id}


@router.post("/approvals/{approval_id}/entries/{entry_id}/reject")
async def reject_entry(
    approval_id: int,
    entry_id: int,
    body: RejectRequest,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
    _license: None = Depends(_require_advanced_approvals),
):
    """Reject a single timesheet entry. Requires advanced_approvals license."""
    # Verify manager has access to this approval
    approval_stmt = select(Approval).where(Approval.approval_id == approval_id)
    approval_result = await db.execute(approval_stmt)
    approval = approval_result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Verify manager has access via organization
    employee_stmt = select(Employee.org_id).where(Employee.employee_id == approval.employee_id)
    employee_result = await db.execute(employee_stmt)
    employee_org_id = employee_result.scalar_one_or_none()
    
    org_stmt = select(Organization.manager_id).where(Organization.org_id == employee_org_id)
    org_result = await db.execute(org_stmt)
    manager_id = org_result.scalar_one_or_none()
    
    if manager_id != current_user["employee_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update entry status
    entry_stmt = (
        select(TimesheetEntry)
        .where(
            TimesheetEntry.timesheet_entry_id == entry_id,
            TimesheetEntry.employee_id == approval.employee_id,
        )
    )
    entry_result = await db.execute(entry_stmt)
    entry = entry_result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.status = "rejected"
    entry.notes = body.rejection_reason
    await db.commit()
    
    return {"message": "Entry rejected", "entry_id": entry_id}


@router.post("/approvals/{approval_id}/entries/{entry_id}/pending")
async def revert_entry_to_pending(
    approval_id: int,
    entry_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
    _license: None = Depends(_require_advanced_approvals),
):
    """Revert a single timesheet entry back to pending (submitted) status. Requires advanced_approvals license."""
    # Verify manager has access to this approval
    approval_stmt = select(Approval).where(Approval.approval_id == approval_id)
    approval_result = await db.execute(approval_stmt)
    approval = approval_result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Verify manager has access via organization
    employee_stmt = select(Employee.org_id).where(Employee.employee_id == approval.employee_id)
    employee_result = await db.execute(employee_stmt)
    employee_org_id = employee_result.scalar_one_or_none()
    
    org_stmt = select(Organization.manager_id).where(Organization.org_id == employee_org_id)
    org_result = await db.execute(org_stmt)
    manager_id = org_result.scalar_one_or_none()
    
    if manager_id != current_user["employee_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update entry status
    entry_stmt = (
        select(TimesheetEntry)
        .where(
            TimesheetEntry.timesheet_entry_id == entry_id,
            TimesheetEntry.employee_id == approval.employee_id,
        )
    )
    entry_result = await db.execute(entry_stmt)
    entry = entry_result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.status = "submitted"
    entry.notes = None
    entry.approved_at = None
    await db.commit()
    
    # Check if approval should be reverted to pending
    # If at least one entry is submitted, the approval should be pending
    week_end = approval.week_start + timedelta(days=6)
    entries_stmt = (
        select(TimesheetEntry.status)
        .where(
            TimesheetEntry.employee_id == approval.employee_id,
            TimesheetEntry.work_date >= approval.week_start,
            TimesheetEntry.work_date <= week_end,
            TimesheetEntry.deleted_at.is_(None),
        )
    )
    entries_result = await db.execute(entries_stmt)
    all_statuses = [row[0] for row in entries_result.all()]
    
    # If any entry is submitted, set approval to pending
    if "submitted" in all_statuses:
        approval.status = "pending"
        approval.decided_at = None
        approval.rejection_reason = None
        await db.commit()
    
    return {"message": "Entry reverted to pending", "entry_id": entry_id}


@router.post("/approvals/{approval_id}/revert-all")
async def revert_all_entries_to_pending(
    approval_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
    _license: None = Depends(_require_advanced_approvals),
):
    """Revert ALL timesheet entries of a week back to pending (submitted) status. Requires advanced_approvals license."""
    # Verify manager has access to this approval
    approval_stmt = select(Approval).where(Approval.approval_id == approval_id)
    approval_result = await db.execute(approval_stmt)
    approval = approval_result.scalar_one_or_none()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Verify manager has access via organization
    employee_stmt = select(Employee.org_id).where(Employee.employee_id == approval.employee_id)
    employee_result = await db.execute(employee_stmt)
    employee_org_id = employee_result.scalar_one_or_none()
    
    org_stmt = select(Organization.manager_id).where(Organization.org_id == employee_org_id)
    org_result = await db.execute(org_stmt)
    manager_id = org_result.scalar_one_or_none()
    
    if manager_id != current_user["employee_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all entries for this week
    week_end = approval.week_start + timedelta(days=6)
    entries_stmt = (
        select(TimesheetEntry)
        .where(
            TimesheetEntry.employee_id == approval.employee_id,
            TimesheetEntry.work_date >= approval.week_start,
            TimesheetEntry.work_date <= week_end,
            TimesheetEntry.deleted_at.is_(None),
        )
    )
    entries_result = await db.execute(entries_stmt)
    entries = entries_result.scalars().all()
    
    # Revert all entries to submitted
    count = 0
    for entry in entries:
        entry.status = "submitted"
        entry.notes = None
        entry.approved_at = None
        count += 1
    
    # Revert approval to pending
    approval.status = "pending"
    approval.decided_at = None
    approval.rejection_reason = None
    approval.notes = None
    
    await db.commit()
    
    return {
        "message": f"All {count} entries reverted to pending",
        "approval_id": approval_id,
        "entries_count": count
    }
