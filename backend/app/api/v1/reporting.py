"""Reporting & Analytics API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.module_license_deps import require_finance_license
from app.services.reporting_service import ReportingService

router = APIRouter(tags=["reporting"])


@router.get("/employee/statistics")
async def employee_statistics(
    period: str = Query("this_month"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ReportingService(db)
    return await svc.get_personal_stats(current_user["employee_id"], period)


@router.get("/manager/team-statistics")
async def manager_team_statistics(
    period: str = Query("this_month"),
    current_user: dict = Depends(require_role("manager", "admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ReportingService(db)
    return await svc.get_team_stats(current_user["employee_id"], period)


@router.get("/manager-dashboard")
async def manager_dashboard(
    period: str = Query("this_month"),
    current_user: dict = Depends(require_role("manager", "admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dashboard stats for managers: KPIs + monthly trend."""
    svc = ReportingService(db)
    return await svc.get_manager_dashboard(current_user["employee_id"], period)


@router.get("/admin/organization-statistics")
async def admin_organization_statistics(
    period: str = Query("this_month"),
    current_user: dict = Depends(require_role("admin", "finance")),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ReportingService(db)
    return await svc.get_financial_report(period=period)


@router.get("/admin/hours-report")
async def admin_hours_report(
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str = Query(..., description="YYYY-MM-DD"),
    employee_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    group_by: str = Query("day", description="day | project | employee | entry_type"),
    current_user: dict = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
) -> list:
    from datetime import date as _date
    try:
        d_from = _date.fromisoformat(date_from)
        d_to = _date.fromisoformat(date_to)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Invalid date format")
    svc = ReportingService(db)
    return await svc.get_hours_report(d_from, d_to, employee_id, project_id, group_by)


@router.get("/finance/client-report")
async def finance_client_report(
    period: str = Query("this_month"),
    client_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_role("finance", "admin")),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ReportingService(db)
    return await svc.get_financial_report(period=period, client_id=client_id)


@router.get("/finance/project-report")
async def finance_project_report(
    project_id: int = Query(...),
    period: str = Query("this_month"),
    current_user: dict = Depends(require_role("finance", "admin")),
    _license: None = Depends(require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ReportingService(db)
    return await svc.get_financial_report(period=period, project_id=project_id)
