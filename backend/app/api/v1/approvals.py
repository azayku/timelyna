"""Approval routes — manager, employee, and admin endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.services.approval_service import ApprovalService

router = APIRouter(tags=["approvals"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ApproveRequest(BaseModel):
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    rejection_reason: str


# ---------------------------------------------------------------------------
# 3.7 — Manager approval routes
# ---------------------------------------------------------------------------

@router.get("/manager/approvals")
async def manager_list_approvals(
    status: str = Query("pending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("manager")),
    db: AsyncSession = Depends(get_db),
) -> list:
    svc = ApprovalService(db)
    if status == "pending":
        return await svc.get_pending_for_manager(
            current_user["employee_id"], page=page, page_size=page_size
        )
    # For non-pending, fall back to employee-scoped view filtered by manager's reports
    # (simplified: return pending_for_manager with all statuses via get_all filtered)
    return await svc.get_pending_for_manager(
        current_user["employee_id"], page=page, page_size=page_size
    )


@router.get("/manager/approvals/{approval_id}")
async def manager_get_approval(
    approval_id: int,
    current_user: dict = Depends(require_role("manager")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ApprovalService(db)
    return await svc.get_by_id_for_manager(current_user["employee_id"], approval_id)


@router.post("/manager/approvals/{approval_id}/approve")
async def manager_approve(
    approval_id: int,
    body: ApproveRequest,
    current_user: dict = Depends(require_role("manager")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ApprovalService(db)
    return await svc.approve(current_user["employee_id"], approval_id, notes=body.notes)


@router.post("/manager/approvals/{approval_id}/reject")
async def manager_reject(
    approval_id: int,
    body: RejectRequest,
    current_user: dict = Depends(require_role("manager")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ApprovalService(db)
    return await svc.reject(
        current_user["employee_id"], approval_id, rejection_reason=body.rejection_reason
    )


# ---------------------------------------------------------------------------
# 3.8 — Employee submission routes
# ---------------------------------------------------------------------------

@router.get("/employee/submissions")
async def employee_list_submissions(
    status: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    svc = ApprovalService(db)
    return await svc.get_by_employee(
        current_user["employee_id"],
        status_filter=status,
        page=page,
        page_size=page_size,
    )


@router.post("/employee/submissions/{approval_id}/cancel")
async def employee_cancel_submission(
    approval_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ApprovalService(db)
    return await svc.cancel(current_user["employee_id"], approval_id)


# ---------------------------------------------------------------------------
# 3.9 — Admin override routes
# ---------------------------------------------------------------------------

@router.get("/admin/approvals")
async def admin_list_approvals(
    status: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("admin", "payroll")),
    db: AsyncSession = Depends(get_db),
) -> list:
    svc = ApprovalService(db)
    return await svc.get_all_admin(status_filter=status, page=page, page_size=page_size)


@router.post("/admin/approvals/{approval_id}/approve")
async def admin_approve(
    approval_id: int,
    body: ApproveRequest,
    current_user: dict = Depends(require_role("admin", "payroll")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ApprovalService(db)
    return await svc.approve(
        current_user["employee_id"], approval_id, notes=body.notes, is_admin=True
    )


@router.post("/admin/approvals/{approval_id}/reject")
async def admin_reject(
    approval_id: int,
    body: RejectRequest,
    current_user: dict = Depends(require_role("admin", "payroll")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ApprovalService(db)
    return await svc.reject(
        current_user["employee_id"],
        approval_id,
        rejection_reason=body.rejection_reason,
        is_admin=True,
    )


# ---------------------------------------------------------------------------
# Detail entries for an approval (manager + admin)
# ---------------------------------------------------------------------------

@router.get("/approvals/{approval_id}/entries")
async def get_approval_entries(
    approval_id: int,
    current_user: dict = Depends(require_role("manager", "admin", "payroll")),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Return all timesheet entries for a given approval week."""
    from sqlalchemy import select
    from app.models.approval import Approval
    from app.models.timesheet_entry import TimesheetEntry
    from app.models.project import Project
    from datetime import timedelta

    # Get approval
    result = await db.execute(select(Approval).where(Approval.approval_id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Approval not found")

    week_end = approval.week_start + timedelta(days=6)

    # Get entries with project name
    result = await db.execute(
        select(TimesheetEntry, Project.project_name)
        .join(Project, Project.project_id == TimesheetEntry.project_id)
        .where(
            TimesheetEntry.employee_id == approval.employee_id,
            TimesheetEntry.work_date >= approval.week_start,
            TimesheetEntry.work_date <= week_end,
            TimesheetEntry.deleted_at.is_(None),
        )
        .order_by(TimesheetEntry.work_date, Project.project_name)
    )
    rows = result.all()

    return [
        {
            "timesheet_entry_id": e.timesheet_entry_id,
            "work_date": str(e.work_date),
            "project_name": pname,
            "entry_type": e.entry_type,
            "hours_worked": float(e.hours_worked),
            "description": e.description,
            "notes": e.notes,
            "billable_flag": e.billable_flag,
            "status": e.status,
        }
        for e, pname in rows
    ]
