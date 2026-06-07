"""Employee timesheet routes — /api/v1/employee/timesheet/..."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.timesheet import (
    CreateEntryRequest,
    SubmitWeekRequest,
    TimesheetEntryResponse,
    UpdateEntryRequest,
)
from app.services.timesheet_service import TimesheetService

router = APIRouter(prefix="/employee/timesheet", tags=["timesheet"])


# 2.15 — GET /employee/timesheet/week?week=2025-W12
@router.get("/week")
async def get_week(
    week: str = Query(..., description="ISO week string, e.g. 2025-W12"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = TimesheetService(db, org_id=current_user.get("org_id", 1))
    return await svc.get_week(current_user["employee_id"], week)


# 2.16 — POST /employee/timesheet/entries
@router.post("/entries", status_code=status.HTTP_201_CREATED)
async def create_entry(
    body: CreateEntryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = TimesheetService(db, org_id=current_user.get("org_id", 1))
    proxy_admin_id = current_user.get("proxy_admin_id") if current_user.get("is_proxy") else None
    return await svc.create_entry(current_user["employee_id"], body.model_dump(), proxy_admin_id=proxy_admin_id)


# 2.17 — PUT /employee/timesheet/entries/{id}
@router.put("/entries/{entry_id}")
async def update_entry(
    entry_id: int,
    body: UpdateEntryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = TimesheetService(db, org_id=current_user.get("org_id", 1))
    return await svc.update_entry(
        current_user["employee_id"], entry_id, body.model_dump(exclude_none=True)
    )


# 2.18 — DELETE /employee/timesheet/entries/{id}
@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Response
    svc = TimesheetService(db, org_id=current_user.get("org_id", 1))
    await svc.delete_entry(current_user["employee_id"], entry_id)
    return _Response(status_code=status.HTTP_204_NO_CONTENT)


# 2.19 — POST /employee/timesheet/submit
@router.post("/submit")
async def submit_week(
    body: SubmitWeekRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = TimesheetService(db, org_id=current_user.get("org_id", 1))
    return await svc.submit_week(current_user["employee_id"], body.week)


# GET /employee/timesheet/drafts — all draft entries for the current employee
@router.get("/drafts", response_model=list[TimesheetEntryResponse])
async def get_draft_entries(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TimesheetService(db, org_id=current_user.get("org_id", 1))
    return await svc.get_draft_entries(current_user["employee_id"])


# GET /employee/timesheet/entries — all entries for the current employee
@router.get("/entries", response_model=list[TimesheetEntryResponse])
async def get_all_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TimesheetService(db, org_id=current_user.get("org_id", 1))
    return await svc.get_all_entries(current_user["employee_id"], skip=skip, limit=limit)
