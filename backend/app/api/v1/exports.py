"""Export routes — async report generation."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.employee import Employee
from app.models.export import Export
from app.models.organization import Organization
from app.models.project import Project
from app.models.timesheet_entry import TimesheetEntry

router = APIRouter(tags=["exports"])


class ExportRequest(BaseModel):
    report_type: str
    format: str  # "pdf" | "csv"
    filters: Optional[dict[str, Any]] = None


@router.post("/exports", status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    body: ExportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    export = Export(
        report_type=body.report_type,
        format=body.format,
        status="pending",
        created_by=current_user["employee_id"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(export)
    await db.flush()
    await db.refresh(export)
    await db.commit()

    # Queue Celery task (stub — logs and sets status=ready)
    try:
        from app.tasks.export_tasks import generate_export
        generate_export.delay(export.id)  # type: ignore[union-attr]
    except Exception:
        # Celery not available — task will be triggered manually in tests
        pass

    return {"export_id": export.id, "status": "pending"}


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from sqlalchemy import select
    result = await db.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")

    if export.status != "ready":
        return {"status": export.status}

    return {"download_url": export.s3_url}


@router.get("/exports/timesheet/pdf")
async def export_timesheet_pdf(
    start_date: date = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Date de fin (YYYY-MM-DD)"),
    project_id: list[int] = Query(default=[], description="Filtrer par projet(s)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Génère et retourne un PDF de rapport de timesheet pour l'employé connecté.

    Args:
        start_date: Date de début de la période
        end_date: Date de fin de la période
        db: Session de base de données
        current_user: Utilisateur authentifié

    Returns:
        Response: PDF en téléchargement direct
    """
    employee_id = current_user["employee_id"]
    org_id = current_user.get("org_id", 1)

    # Récupérer les informations de l'employé
    employee_result = await db.execute(
        select(Employee).where(
            Employee.employee_id == employee_id, Employee.deleted_at.is_(None)
        )
    )
    employee = employee_result.scalar_one_or_none()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    employee_name = f"{employee.first_name} {employee.last_name}"

    # Récupérer l'organisation
    org_result = await db.execute(
        select(Organization).where(
            Organization.org_id == org_id, Organization.deleted_at.is_(None)
        )
    )
    org = org_result.scalar_one_or_none()
    org_name = org.org_name if org else "Organisation"

    # Récupérer les entrées timesheet de la période
    filters = [
        TimesheetEntry.employee_id == employee_id,
        TimesheetEntry.work_date >= start_date,
        TimesheetEntry.work_date <= end_date,
        TimesheetEntry.deleted_at.is_(None),
        Project.deleted_at.is_(None),
    ]
    if project_id:
        filters.append(TimesheetEntry.project_id.in_(project_id))

    stmt = (
        select(TimesheetEntry, Project)
        .join(Project, TimesheetEntry.project_id == Project.project_id)
        .where(*filters)
        .order_by(TimesheetEntry.work_date)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Préparer les données pour le PDF
    entries_data = []
    for entry, project in rows:
        entries_data.append(
            {
                "work_date": entry.work_date,
                "project_id": entry.project_id,
                "project_name": project.project_name,
                "task_type": entry.task_type,
                "hours_worked": entry.hours_worked,
                "description": entry.description,
                "status": entry.status,
            }
        )

    # Générer le PDF
    from app.services.pdf_service import PDFService

    pdf_service = PDFService()
    pdf_bytes = pdf_service.generate_timesheet_pdf(
        employee_name=employee_name,
        org_name=org_name,
        entries=entries_data,
        period_start=start_date,
        period_end=end_date,
    )

    filename = f"timesheet_{employee_id}_{start_date}_{end_date}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/hours-report/pdf")
async def export_hours_report_pdf(
    start_date: date = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Date de fin (YYYY-MM-DD)"),
    project_id: list[int] = Query(default=[], description="Filtrer par projet(s)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Génère un PDF du rapport d'heures pour admin/manager.

    Args:
        start_date: Date de début
        end_date: Date de fin
        project_id: Liste optionnelle de projets à inclure
    """
    from app.models.employee import Employee as Emp

    role = current_user.get("role", "employee")
    if role not in ("admin", "manager"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Accès réservé aux admins et managers")

    org_id = current_user.get("org_id", 1)

    # Récupérer l'organisation
    org_result = await db.execute(
        select(Organization).where(
            Organization.org_id == org_id, Organization.deleted_at.is_(None)
        )
    )
    org = org_result.scalar_one_or_none()
    org_name = org.org_name if org else "Organisation"

    # Construire les filtres
    filters = [
        TimesheetEntry.work_date >= start_date,
        TimesheetEntry.work_date <= end_date,
        TimesheetEntry.deleted_at.is_(None),
        Project.deleted_at.is_(None),
        Emp.deleted_at.is_(None),
    ]
    if project_id:
        filters.append(TimesheetEntry.project_id.in_(project_id))

    # Pour les managers : limiter à leur équipe
    if role == "manager":
        from app.models.employee import Employee as EmpModel
        from sqlalchemy import and_
        manager_id = current_user["employee_id"]
        # Sous-requête : employés dont le manager_id correspond
        filters.append(Emp.manager_id == manager_id)

    stmt = (
        select(TimesheetEntry, Project, Emp)
        .join(Project, TimesheetEntry.project_id == Project.project_id)
        .join(Emp, TimesheetEntry.employee_id == Emp.employee_id)
        .where(*filters)
        .order_by(Emp.last_name, Emp.first_name, TimesheetEntry.work_date)
    )

    result = await db.execute(stmt)
    rows = result.all()

    entries_data = []
    for entry, project, emp in rows:
        entries_data.append(
            {
                "work_date": entry.work_date,
                "employee_name": f"{emp.first_name} {emp.last_name}",
                "project_name": project.project_name,
                "task_type": entry.task_type,
                "hours_worked": entry.hours_worked,
                "description": entry.description,
                "status": entry.status,
            }
        )

    from app.services.pdf_service import PDFService

    pdf_service = PDFService()
    pdf_bytes = pdf_service.generate_hours_report_pdf(
        org_name=org_name,
        entries=entries_data,
        period_start=start_date,
        period_end=end_date,
    )

    filename = f"rapport_heures_{start_date}_{end_date}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
