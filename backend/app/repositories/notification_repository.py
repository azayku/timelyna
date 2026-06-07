"""NotificationRepository — DB access for notifications and preferences."""
from __future__ import annotations

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self,
        employee_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Notification]:
        q = select(Notification).where(Notification.employee_id == employee_id)
        if unread_only:
            q = q.where(Notification.is_read.is_(False))
        q = q.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: int, employee_id: int) -> bool:
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.employee_id == employee_id,
            )
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def mark_all_read(self, employee_id: int) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.employee_id == employee_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount

    async def get_preferences(self, employee_id: int) -> list[NotificationPreference]:
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.employee_id == employee_id
            )
        )
        return list(result.scalars().all())

    async def upsert_preference(
        self,
        employee_id: int,
        type: str,
        email_enabled: bool,
        in_app_enabled: bool,
    ) -> NotificationPreference:
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.employee_id == employee_id,
                NotificationPreference.type == type,
            )
        )
        pref = result.scalar_one_or_none()
        if pref is None:
            pref = NotificationPreference(
                employee_id=employee_id,
                type=type,
                email_enabled=email_enabled,
                in_app_enabled=in_app_enabled,
            )
            self.db.add(pref)
        else:
            pref.email_enabled = email_enabled
            pref.in_app_enabled = in_app_enabled
        await self.db.flush()
        await self.db.refresh(pref)
        return pref
