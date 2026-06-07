"""Notification routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.notification_repository import NotificationRepository

router = APIRouter(tags=["notifications"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class NotificationOut(BaseModel):
    id: int
    employee_id: int
    type: str
    title: str
    message: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    action_url: Optional[str] = None
    is_read: bool
    created_at: str

    model_config = {"from_attributes": True}


class PreferenceOut(BaseModel):
    id: int
    employee_id: int
    type: str
    email_enabled: bool
    in_app_enabled: bool

    model_config = {"from_attributes": True}


class PreferenceIn(BaseModel):
    type: str
    email_enabled: bool = True
    in_app_enabled: bool = True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(
    unread: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    repo = NotificationRepository(db)
    skip = (page - 1) * page_size
    notifications = await repo.list(
        employee_id=current_user["employee_id"],
        unread_only=unread,
        skip=skip,
        limit=page_size,
    )
    return [
        {
            "id": n.id,
            "employee_id": n.employee_id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "related_entity_type": n.related_entity_type,
            "related_entity_id": n.related_entity_id,
            "action_url": n.action_url,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = NotificationRepository(db)
    updated = await repo.mark_read(notification_id, current_user["employee_id"])
    return {"updated": updated}


@router.post("/notifications/read-all")
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = NotificationRepository(db)
    count = await repo.mark_all_read(current_user["employee_id"])
    return {"updated": count}


@router.get("/notifications/preferences", response_model=list[PreferenceOut])
async def get_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    repo = NotificationRepository(db)
    prefs = await repo.get_preferences(current_user["employee_id"])
    return [
        {
            "id": p.id,
            "employee_id": p.employee_id,
            "type": p.type,
            "email_enabled": p.email_enabled,
            "in_app_enabled": p.in_app_enabled,
        }
        for p in prefs
    ]


@router.put("/notifications/preferences")
async def update_preferences(
    body: list[PreferenceIn],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    repo = NotificationRepository(db)
    results = []
    for item in body:
        pref = await repo.upsert_preference(
            employee_id=current_user["employee_id"],
            type=item.type,
            email_enabled=item.email_enabled,
            in_app_enabled=item.in_app_enabled,
        )
        results.append({
            "id": pref.id,
            "employee_id": pref.employee_id,
            "type": pref.type,
            "email_enabled": pref.email_enabled,
            "in_app_enabled": pref.in_app_enabled,
        })
    await db.commit()
    return results
