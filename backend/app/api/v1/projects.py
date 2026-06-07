"""Projects reference data route — /api/v1/projects"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.project_repository import ProjectRepository
from app.schemas.timesheet import ProjectResponse, ProjectBudgetStatus

router = APIRouter(prefix="/projects", tags=["projects"])


# 2.20 — GET /projects?active=true&date=YYYY-MM-DD
@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    active: bool = Query(default=True),
    date: date | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    repo = ProjectRepository(db)
    role = current_user.get("role", "employee")
    employee_id = current_user["employee_id"]

    if role in ("admin", "finance"):
        projects = await repo.list_all_active() if active else await repo.list_all_active(limit=1000)
        # Convert ORM objects to dicts for admin/finance (no client info needed for now)
        return [ProjectResponse.model_validate(p) for p in projects]
    else:
        # Returns list of dicts with client info
        projects = await repo.list_active_for_employee(employee_id, reference_date=date)
        return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/budget-overview", response_model=list[ProjectBudgetStatus])
async def get_all_projects_budget(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[ProjectBudgetStatus]:
    """Retourne l'état budget de tous les projets avec client, manager et consommation."""
    from app.models.project import Project
    from app.models.timesheet_entry import TimesheetEntry
    from app.models.client import Client
    from app.models.employee import Employee

    # Récupérer tous les projets avec budget + client + manager en une seule requête
    proj_result = await db.execute(
        select(Project, Client, Employee)
        .outerjoin(Client, Project.client_id == Client.client_id)
        .outerjoin(Employee, Project.manager_id == Employee.employee_id)
        .where(
            Project.deleted_at.is_(None),
            Project.budget_hours.is_not(None),
        )
    )
    projects_rows = proj_result.all()

    result = []
    for p, client, manager in projects_rows:
        # Calculer les heures consommées
        hours_result = await db.execute(
            select(func.sum(TimesheetEntry.hours_worked)).where(
                TimesheetEntry.project_id == p.project_id,
                TimesheetEntry.status.not_in(["rejected", "draft"]),
                TimesheetEntry.deleted_at.is_(None),
            )
        )
        consumed = float(hours_result.scalar() or 0.0)
        budget = float(p.budget_hours) if p.budget_hours else None
        threshold = float(p.budget_alert_threshold or Decimal("0.8"))

        remaining = (budget - consumed) if budget else None
        pct = (consumed / budget * 100) if budget and budget > 0 else None
        alert = pct is not None and (pct / 100) >= threshold

        result.append(ProjectBudgetStatus(
            project_id=p.project_id,
            project_name=p.project_name,
            client_id=client.client_id if client else None,
            client_name=client.client_name if client else None,
            manager_id=manager.employee_id if manager else None,
            manager_name=f"{manager.first_name} {manager.last_name}" if manager else None,
            budget_hours=float(p.budget_hours),
            consumed_hours=consumed,
            remaining_hours=remaining,
            consumption_percentage=round(pct, 1) if pct is not None else None,
            alert=alert,
        ))

    return result


@router.get("/{project_id}/budget", response_model=ProjectBudgetStatus)
async def get_project_budget(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ProjectBudgetStatus:
    """Retourne l'état du budget d'un projet spécifique."""
    org_id = current_user.get("org_id", 1)
    from app.models.project import Project
    from app.models.timesheet_entry import TimesheetEntry
    
    # Récupérer le projet
    proj_result = await db.execute(
        select(Project).where(
            Project.project_id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Calculer les heures consommées (somme des entrées timesheet non rejetées)
    hours_result = await db.execute(
        select(func.sum(TimesheetEntry.hours_worked)).where(
            TimesheetEntry.project_id == project_id,
            TimesheetEntry.status.not_in(["REJECTED", "DRAFT"]),
            TimesheetEntry.deleted_at.is_(None),
        )
    )
    consumed = float(hours_result.scalar() or 0.0)
    
    budget = float(project.budget_hours) if project.budget_hours else None
    threshold = float(project.budget_alert_threshold or Decimal("0.8"))
    remaining = (budget - consumed) if budget else None
    pct = (consumed / budget * 100) if budget and budget > 0 else None
    alert = pct is not None and (pct / 100) >= threshold
    
    return ProjectBudgetStatus(
        project_id=project.project_id,
        project_name=project.project_name,
        budget_hours=project.budget_hours,
        consumed_hours=Decimal(str(consumed)),
        remaining_hours=Decimal(str(remaining)) if remaining is not None else None,
        consumption_percentage=round(pct, 1) if pct is not None else None,
        alert=alert,
    )
