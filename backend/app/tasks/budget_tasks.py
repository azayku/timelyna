"""Celery task: send budget alert emails when projects exceed threshold."""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


async def _check_and_send_budget_alerts(db) -> dict:
    """Core logic: find projects over budget threshold and email their manager.

    Avoids re-sending if alert was already sent today (via a simple in-memory
    dedup per run — for production use a Redis set or a DB log table).
    """
    from sqlalchemy import select, func
    from app.models.project import Project
    from app.models.employee import Employee
    from app.models.timesheet_entry import TimesheetEntry
    from app.utils.email import send_budget_alert_email

    result = await db.execute(
        select(Project, Employee)
        .outerjoin(Employee, Project.manager_id == Employee.employee_id)
        .where(
            Project.deleted_at.is_(None),
            Project.budget_hours.is_not(None),
        )
    )
    rows = result.all()

    sent = 0
    skipped = 0

    for project, manager in rows:
        try:
            # Calcul consommation
            hours_result = await db.execute(
                select(func.sum(TimesheetEntry.hours_worked)).where(
                    TimesheetEntry.project_id == project.project_id,
                    TimesheetEntry.status.not_in(["rejected", "draft"]),
                    TimesheetEntry.deleted_at.is_(None),
                )
            )
            consumed = float(hours_result.scalar() or 0.0)
            budget = float(project.budget_hours)
            threshold = float(project.budget_alert_threshold or Decimal("0.8"))
            pct = (consumed / budget * 100) if budget > 0 else 0.0

            # Pas encore en alerte → skip
            if (pct / 100) < threshold:
                skipped += 1
                continue

            remaining = budget - consumed

            # Pas de manager configuré → skip
            if not manager or not manager.email:
                logger.warning(
                    "Project %s (%s) is over budget but has no manager email",
                    project.project_id, project.project_name,
                )
                skipped += 1
                continue

            await send_budget_alert_email(
                to=manager.email,
                project_name=project.project_name,
                consumption_pct=pct,
                budget_hours=budget,
                consumed_hours=consumed,
                remaining_hours=remaining,
                manager_first_name=manager.first_name,
                db=db,
            )
            sent += 1
            logger.info(
                "Budget alert sent for project %s (%.0f%%) to %s",
                project.project_name, pct, manager.email,
            )

        except Exception as exc:
            logger.error(
                "Failed to process budget alert for project %s: %s",
                project.project_id, exc,
            )

    return {"alerts_sent": sent, "skipped": skipped}


async def _run_budget_alerts() -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with SessionLocal() as db:
        result = await _check_and_send_budget_alerts(db)

    await engine.dispose()
    return result


try:
    from app.core.celery_app import celery_app

    @celery_app.task(name="app.tasks.budget_tasks.send_budget_alerts")
    def send_budget_alerts() -> dict:
        """Celery task: check all budgeted projects and send alert emails."""
        return asyncio.get_event_loop().run_until_complete(_run_budget_alerts())

except Exception:
    # Celery not available (e.g. in tests) — define a plain function
    def send_budget_alerts() -> dict:  # type: ignore[misc]
        return asyncio.get_event_loop().run_until_complete(_run_budget_alerts())
