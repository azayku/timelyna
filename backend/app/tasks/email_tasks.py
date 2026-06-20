"""Celery async email tasks -- language-aware via employee.preferred_language."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.celery_app import celery_app
from app.core.database import _get_engine  # type: ignore[attr-defined]
from app.utils.email import (
    send_password_changed_email,
    send_password_reset_email,
    send_welcome_email,
)

logger = logging.getLogger(__name__)

# Supported languages; fallback to 'fr' for anything unknown
SUPPORTED_LANGS = {"fr", "en", "it"}


def _resolve_lang(lang: str | None) -> str:
    """Return a supported language code, defaulting to 'fr'."""
    if lang and lang in SUPPORTED_LANGS:
        return lang
    return "fr"


def _template(base: str, lang: str) -> str:
    """Return language-suffixed template name, e.g. welcome_new_employee_en."""
    resolved = _resolve_lang(lang)
    if resolved == "fr":
        return base  # French is the default - no suffix needed
    return f"{base}_{resolved}"


@celery_app.task(name="tasks.send_reset_email")
def task_send_reset_email(
    to: str,
    reset_link: str,
    first_name: str = "",
    last_name: str = "",
    lang: str = "fr",
) -> None:
    async def _run():
        factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
        async with factory() as db:
            await send_password_reset_email(
                to, reset_link, first_name, last_name, db,
                template_name=_template("password_reset", lang),
            )
    asyncio.run(_run())


@celery_app.task(name="tasks.send_password_changed_email")
def task_send_password_changed_email(to: str, lang: str = "fr") -> None:
    send_password_changed_email(to, lang=_resolve_lang(lang))


@celery_app.task(name="tasks.send_welcome_email")
def task_send_welcome_email(
    to: str,
    setup_link: str,
    first_name: str = "",
    last_name: str = "",
    username: str = "",
    lang: str = "fr",
) -> None:
    async def _run():
        factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
        async with factory() as db:
            await send_welcome_email(
                to, setup_link, first_name, last_name, username, db,
                template_name=_template("welcome_new_employee", lang),
            )
    asyncio.run(_run())


@celery_app.task(name="tasks.send_deactivation_warning_email")
def task_send_deactivation_warning_email(to: str, scheduled_at: str, lang: str = "fr") -> None:
    logger.info(
        "Deactivation warning email to %s (scheduled: %s, lang: %s)",
        to, scheduled_at, _resolve_lang(lang),
    )


@celery_app.task(name="tasks.send_mutation_notification")
def task_send_mutation_notification(
    employee_id: int,
    target_org_id: int,
    mutated_by: int,
) -> None:
    """Send email to the new org manager when an employee is mutated."""
    async def _run():
        factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
        async with factory() as db:
            from sqlalchemy import select as _sel
            from app.models.employee import Employee
            from app.models.organization import Organization
            from app.utils.email import send_email

            org_result = await db.execute(
                _sel(Organization).where(Organization.org_id == target_org_id)
            )
            org = org_result.scalar_one_or_none()
            if not org:
                return

            manager_result = await db.execute(
                _sel(Employee).where(Employee.employee_id == org.manager_id)
            )
            manager = manager_result.scalar_one_or_none()
            if not manager or not manager.email:
                return

            emp_result = await db.execute(
                _sel(Employee).where(Employee.employee_id == employee_id)
            )
            emp = emp_result.scalar_one_or_none()
            emp_name = f"{emp.first_name} {emp.last_name}" if emp else str(employee_id)

            subject = f"[Timelyna] Mutation vers {org.org_name}"
            body = (
                f"Bonjour {manager.first_name},\n\n"
                f"L'employe {emp_name} a ete mute vers votre organisation ({org.org_name}).\n\n"
                "Cordialement,\nTimelyna"
            )
            send_email(to=manager.email, subject=subject, body=body)

    asyncio.run(_run())
