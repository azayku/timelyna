"""Finance Pro API routes — /api/v1/finance/..."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.module_license_deps import require_finance_license
from app.core.security import require_role

router = APIRouter(prefix="/finance", tags=["finance"])

_finance_license = require_finance_license
_finance_role = require_role("finance", "admin")


# ---------------------------------------------------------------------------
# US-02 — Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard")
async def get_finance_dashboard(
    period: str = Query(default="this_month"),
    _lic: None = Depends(_finance_license),
    current_user: dict = Depends(_finance_role),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.finance_dashboard_service import FinanceDashboardService
    svc = FinanceDashboardService(db)
    org_id = current_user.get("org_id", 1)
    return await svc.get_dashboard(org_id=org_id, period=period)


# ---------------------------------------------------------------------------
# US-03 — Invoice mark paid
# ---------------------------------------------------------------------------

class MarkPaidRequest(BaseModel):
    paid_at: Optional[datetime] = None


@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: int,
    body: MarkPaidRequest = MarkPaidRequest(),
    _lic: None = Depends(_finance_license),
    current_user: dict = Depends(_finance_role),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.invoicing_service import InvoicingService
    svc = InvoicingService(db)
    performed_by = current_user.get("employee_id")
    return await svc.mark_paid(invoice_id, paid_at=body.paid_at, performed_by=performed_by)


@router.get("/invoices/{invoice_id}/audit-logs")
async def get_invoice_audit_logs(
    invoice_id: int,
    _lic: None = Depends(_finance_license),
    _: dict = Depends(_finance_role),
    db: AsyncSession = Depends(get_db),
) -> list:
    from app.services.invoicing_service import InvoicingService
    svc = InvoicingService(db)
    return await svc.get_audit_logs(invoice_id)


# ---------------------------------------------------------------------------
# US-04 — Financial reports
# ---------------------------------------------------------------------------

@router.get("/reports/pnl")
async def get_pnl(
    period: str = Query(default="this_month"),
    _lic: None = Depends(_finance_license),
    _: dict = Depends(_finance_role),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.reporting_service import ReportingService
    svc = ReportingService(db)
    return await svc.get_pnl(period=period)


@router.get("/reports/profitability")
async def get_project_profitability(
    _lic: None = Depends(_finance_license),
    _: dict = Depends(_finance_role),
    db: AsyncSession = Depends(get_db),
) -> list:
    from app.services.reporting_service import ReportingService
    svc = ReportingService(db)
    return await svc.get_project_profitability()


@router.get("/reports/aging")
async def get_aging_report(
    _lic: None = Depends(_finance_license),
    _: dict = Depends(_finance_role),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.reporting_service import ReportingService
    svc = ReportingService(db)
    return await svc.get_aging_report()


@router.get("/reports/cashflow")
async def get_cashflow_forecast(
    months: int = Query(default=3, ge=1, le=12),
    _lic: None = Depends(_finance_license),
    _: dict = Depends(_finance_role),
    db: AsyncSession = Depends(get_db),
) -> list:
    from app.services.reporting_service import ReportingService
    svc = ReportingService(db)
    return await svc.get_cashflow_forecast(months=months)
