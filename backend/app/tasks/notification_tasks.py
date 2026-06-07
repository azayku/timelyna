"""Notification Celery tasks and async helpers."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Supported languages; fallback to 'fr' for anything unknown
_SUPPORTED_LANGS = {'fr', 'en', 'it'}


def _resolve_lang(lang: str | None) -> str:
    """Return a supported language code, defaulting to 'fr'."""
    if lang and lang in _SUPPORTED_LANGS:
        return lang
    return 'fr'


def _approval_template(status: str, lang: str) -> str:
    """Return the email template name for an approval notification.

    Examples:
      ('approved', 'fr') -> 'approval_approved_fr'
      ('rejected', 'en') -> 'approval_rejected_en'
      ('approved', 'xx') -> 'approval_approved_fr'  (fallback)
    """
    resolved = _resolve_lang(lang)
    return f"approval_{status}_{resolved}"


async def run_send_email(to: str, subject: str, template_name: str, context: dict) -> None:
    """Stub: log the email. In production: render Jinja2 template + send via SMTP."""
    logger.info("EMAIL [%s] to=%s subject=%s", template_name, to, subject)


async def run_create_in_app_notification(
    employee_id: int,
    type: str,
    title: str,
    message: str,
    entity_type: str | None,
    entity_id: int | None,
    db,
) -> None:
    """Create a Notification record in DB."""
    from app.models.notification import Notification

    notif = Notification(
        employee_id=employee_id,
        type=type,
        title=title,
        message=message,
        related_entity_type=entity_type,
        related_entity_id=entity_id,
    )
    db.add(notif)
    await db.flush()


async def run_check_budget_warnings(db) -> list[dict]:
    """Check all active projects for budget warnings.

    Returns list of {project_id, project_name, manager_id, pct, level}
    """
    from sqlalchemy import text

    result = await db.execute(text("""
        SELECT
            p.project_id,
            p.project_name,
            p.manager_id,
            p.budget_hours,
            COALESCE(SUM(te.hours_worked), 0) AS actual_hours
        FROM projects p
        LEFT JOIN timesheet_entries te
            ON te.project_id = p.project_id
            AND te.status IN ('approved', 'invoiced')
            AND te.deleted_at IS NULL
        WHERE p.deleted_at IS NULL
          AND p.budget_hours IS NOT NULL
          AND p.budget_hours > 0
        GROUP BY p.project_id, p.project_name, p.manager_id, p.budget_hours
        HAVING actual_hours >= p.budget_hours * 0.8
    """))
    warnings = []
    for row in result.mappings().all():
        pct = float(row["actual_hours"]) / float(row["budget_hours"]) * 100
        level = "critical" if pct >= 100 else "warning"
        warnings.append({
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "manager_id": row["manager_id"],
            "pct": round(pct, 1),
            "level": level,
        })
    return warnings


# ---------------------------------------------------------------------------
# Celery tasks (optional — graceful fallback when Celery/Redis not available)
# ---------------------------------------------------------------------------

try:
    from celery import Celery
    from app.core.config import get_settings

    _settings = get_settings()
    celery_app = Celery("timesheetpro", broker=_settings.REDIS_URL)

    @celery_app.task(name="tasks.send_email_notification")
    def send_email_notification(to: str, subject: str, template_name: str, context: dict) -> None:
        import asyncio
        asyncio.run(run_send_email(to, subject, template_name, context))

    @celery_app.task(name="tasks.create_in_app_notification")
    def create_in_app_notification(
        employee_id: int,
        type: str,
        title: str,
        message: str,
        entity_type: str | None,
        entity_id: int | None,
    ) -> None:
        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from app.core.database import _get_engine  # type: ignore[attr-defined]

        async def _run():
            factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
            async with factory() as db:
                await run_create_in_app_notification(
                    employee_id, type, title, message, entity_type, entity_id, db
                )
                await db.commit()

        asyncio.run(_run())

    @celery_app.task(name="tasks.check_budget_warnings")
    def check_budget_warnings() -> list[dict]:
        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from app.core.database import _get_engine  # type: ignore[attr-defined]

        async def _run():
            factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
            async with factory() as db:
                return await run_check_budget_warnings(db)

        return asyncio.run(_run())

    @celery_app.task(name="tasks.send_approval_notification")
    def task_send_approval_notification(
        employee_id: int,
        approval_id: int,
        status: str,
        week_start: str,
        lang: str = "fr",
    ) -> None:
        """Send approval/rejection email to the employee in their preferred language."""
        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from app.core.database import _get_engine  # type: ignore[attr-defined]

        template = _approval_template(status, lang)

        async def _run():
            factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
            async with factory() as db:
                from sqlalchemy import select as _sel
                from app.models.employee import Employee

                result = await db.execute(
                    _sel(Employee).where(Employee.employee_id == employee_id)
                )
                emp = result.scalar_one_or_none()
                if not emp or not emp.email:
                    logger.warning("task_send_approval_notification: employee %s not found", employee_id)
                    return

                subject_map = {
                    "approved": {
                        "fr": "Votre feuille de temps a été approuvée",
                        "en": "Your timesheet has been approved",
                        "it": "Il tuo foglio presenze è stato approvato",
                    },
                    "rejected": {
                        "fr": "Votre feuille de temps a été rejetée",
                        "en": "Your timesheet has been rejected",
                        "it": "Il tuo foglio presenze è stato rifiutato",
                    },
                }
                resolved = _resolve_lang(lang)
                subject = subject_map.get(status, {}).get(resolved, f"Timesheet {status}")
                context = {
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "week_start": week_start,
                    "approval_id": approval_id,
                    "status": status,
                }
                await run_send_email(emp.email, subject, template, context)

        asyncio.run(_run())

except Exception:  # noqa: BLE001
    logger.warning("Celery not available — notification tasks disabled (use run_* helpers directly)")

    def send_email_notification(to: str, subject: str, template_name: str, context: dict) -> None:  # type: ignore[misc]
        logger.info("send_email_notification stub: to=%s subject=%s", to, subject)

    def create_in_app_notification(  # type: ignore[misc]
        employee_id: int,
        type: str,
        title: str,
        message: str,
        entity_type: str | None,
        entity_id: int | None,
    ) -> None:
        logger.info("create_in_app_notification stub: employee_id=%s type=%s", employee_id, type)

    def check_budget_warnings() -> list[dict]:  # type: ignore[misc]
        logger.info("check_budget_warnings stub (no Celery)")
        return []

    def task_send_approval_notification(  # type: ignore[misc]
        employee_id: int,
        approval_id: int,
        status: str,
        week_start: str,
        lang: str = "fr",
    ) -> None:
        template = _approval_template(status, lang)
        logger.info(
            "task_send_approval_notification stub: employee_id=%s approval_id=%s status=%s template=%s",
            employee_id, approval_id, status, template,
        )
