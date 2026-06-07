"""Celery task: process scheduled employee deactivations."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def _deactivate_due_employees(db) -> int:
    """Core logic: deactivate employees whose deactivation_scheduled_at <= now.

    Accepts an existing AsyncSession so it can be called from tests without
    opening a new database connection.
    """
    from sqlalchemy import select, update
    from app.models.employee import Employee
    from app.models.auth import RefreshToken

    now = datetime.now(timezone.utc)
    count = 0

    result = await db.execute(
        select(Employee).where(
            Employee.deactivation_scheduled_at <= now,
            Employee.employment_status == "active",
            Employee.deleted_at.is_(None),
        )
    )
    employees = result.scalars().all()

    for emp in employees:
        # Deactivate
        await db.execute(
            update(Employee)
            .where(Employee.employee_id == emp.employee_id)
            .values(
                employment_status="inactive",
                deactivation_scheduled_at=None,
            )
        )
        # Revoke all refresh tokens
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.employee_id == emp.employee_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        count += 1
        logger.info("Deactivated employee %s (%s)", emp.employee_id, emp.email)

    await db.commit()
    return count


async def _run_deactivations() -> int:
    """Async core: open a fresh DB connection and run deactivations.

    Used by the Celery task in production. Tests should call
    _deactivate_due_employees(db) directly with the test session.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with SessionLocal() as db:
        count = await _deactivate_due_employees(db)

    await engine.dispose()
    return count


try:
    from celery import shared_task

    @shared_task(name="app.tasks.deactivation_tasks.process_scheduled_deactivations")
    def process_scheduled_deactivations() -> dict:
        """Désactive les employés dont deactivation_scheduled_at <= now."""
        count = asyncio.run(_run_deactivations())
        logger.info("process_scheduled_deactivations: %d employee(s) deactivated", count)
        return {"deactivated": count}

except Exception:  # noqa: BLE001
    logger.warning("Celery not available — deactivation_tasks running in fallback mode")

    def process_scheduled_deactivations() -> dict:  # type: ignore[misc]
        count = asyncio.run(_run_deactivations())
        return {"deactivated": count}
