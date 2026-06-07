"""Routes d'import CSV — /api/v1/admin/import/..."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.services.import_service import ImportService

router = APIRouter(prefix="/admin/import", tags=["Import"])

_admin_only = require_role("admin")


class ImportResult(BaseModel):
    """Résultat d'un import CSV."""

    success: int
    skipped: int
    errors: list[str]
    message: str


@router.post("/employees", response_model=ImportResult, status_code=status.HTTP_200_OK)
async def import_employees(
    file: UploadFile = File(...),
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ImportResult:
    """
    Importe des employés depuis un fichier CSV.

    Colonnes attendues: email, first_name, last_name
    Colonnes optionnelles: role, phone, department, hire_date

    Les employés existants (même email) sont ignorés.
    Un username et mot de passe temporaire sont générés automatiquement.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Format CSV requis (.csv)"
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB max
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (max 5MB)",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide"
        )

    org_id = current_user.get("org_id", 1)
    svc = ImportService(db, org_id=org_id)
    result = await svc.import_employees_csv(content)

    return ImportResult(
        success=result["success"],
        skipped=result["skipped"],
        errors=result["errors"],
        message=f"{result['success']} employé(s) créé(s), {result['skipped']} ignoré(s)",
    )


@router.post("/projects", response_model=ImportResult, status_code=status.HTTP_200_OK)
async def import_projects(
    file: UploadFile = File(...),
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ImportResult:
    """
    Importe des projets depuis un fichier CSV.

    Colonnes attendues: project_name, project_code, client_name (ou client_id)
    Colonnes optionnelles: description, start_date, end_date, budget_hours, manager_email, billing_rate

    Les projets existants (même project_code) sont ignorés.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Format CSV requis (.csv)"
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (max 5MB)",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide"
        )

    org_id = current_user.get("org_id", 1)
    svc = ImportService(db, org_id=org_id)
    result = await svc.import_projects_csv(content)

    return ImportResult(
        success=result["success"],
        skipped=result["skipped"],
        errors=result["errors"],
        message=f"{result['success']} projet(s) créé(s), {result['skipped']} ignoré(s)",
    )


@router.get("/employees/template", status_code=status.HTTP_200_OK)
async def download_employees_template(_: dict = Depends(_admin_only)) -> Response:
    """Télécharge un fichier CSV template pour l'import d'employés."""
    csv_content = (
        "email,first_name,last_name,role,phone,department,hire_date\n"
        "john.doe@example.com,John,Doe,employee,+33612345678,IT,2026-01-15\n"
        "jane.smith@example.com,Jane,Smith,manager,+33698765432,Finance,2025-12-01\n"
    )
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=template_employees.csv"},
    )


@router.get("/projects/template", status_code=status.HTTP_200_OK)
async def download_projects_template(_: dict = Depends(_admin_only)) -> Response:
    """Télécharge un fichier CSV template pour l'import de projets."""
    csv_content = (
        "project_name,project_code,client_name,description,start_date,end_date,budget_hours,manager_email,billing_rate\n"
        "Projet Alpha,ALPHA-2026,Acme Corp,Développement application mobile,2026-01-01,2026-12-31,1600,manager@example.com,85.00\n"
        "Projet Beta,BETA-2026,Beta Inc,Refonte site web,2026-02-01,,800,manager@example.com,90.00\n"
    )
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=template_projects.csv"},
    )
