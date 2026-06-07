"""Timer API endpoints — /api/v1/timer/..."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.timer import TimerResponse, TimerStart, TimerStopResponse
from app.services.timer_service import TimerService

router = APIRouter(prefix="/timer", tags=["Timer"])


@router.post("/start", response_model=TimerResponse)
async def start_timer(
    payload: TimerStart,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TimerResponse:
    """Start a new timer for the current employee."""
    service = TimerService(db, org_id=current_user.get("org_id", 1))
    timer = await service.start_timer(
        employee_id=current_user["employee_id"],
        project_id=payload.project_id,
        description=payload.description,
        task_type=payload.task_type,
    )

    # Calculer elapsed_seconds pour la réponse
    now = datetime.now(timezone.utc)
    started_at_utc = timer.started_at
    if started_at_utc.tzinfo is None:
        started_at_utc = started_at_utc.replace(tzinfo=timezone.utc)
    elapsed_seconds = int((now - started_at_utc).total_seconds())

    response = TimerResponse.model_validate(timer)
    response.elapsed_seconds = elapsed_seconds
    return response


@router.get("/active", response_model=Optional[TimerResponse])
async def get_active_timer(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Optional[TimerResponse]:
    """Get the active timer for the current employee."""
    service = TimerService(db, org_id=current_user.get("org_id", 1))
    timer = await service.get_active_timer(current_user["employee_id"])

    if not timer:
        return None

    # Calculer elapsed_seconds
    now = datetime.now(timezone.utc)
    started_at_utc = timer.started_at
    if started_at_utc.tzinfo is None:
        started_at_utc = started_at_utc.replace(tzinfo=timezone.utc)
    elapsed_seconds = int((now - started_at_utc).total_seconds())

    response = TimerResponse.model_validate(timer)
    response.elapsed_seconds = elapsed_seconds
    return response


@router.post("/stop", response_model=TimerStopResponse)
async def stop_timer(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TimerStopResponse:
    """Stop the active timer and create a timesheet entry if duration >= 1 minute."""
    service = TimerService(db, org_id=current_user.get("org_id", 1))
    result = await service.stop_timer(current_user["employee_id"])

    if not result["stopped"]:
        raise HTTPException(status_code=404, detail="Aucun timer actif")

    return TimerStopResponse(
        message="Timer arrêté",
        hours_worked=result["hours_worked"],
        timesheet_entry_id=result["timesheet_entry_id"],
    )
