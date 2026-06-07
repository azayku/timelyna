"""Celery tasks for deferred employee onboarding."""
from __future__ import annotations

import asyncio
import logging
from datetime import date

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.onboarding_tasks.activate_pending_employees")
def activate_pending_employees() -> dict:
    """Activate all pending employees whose account_creation_date <= today."""
    return asyncio.get_event_loop().run_until_complete(_activate_pending())


async def _activate_pending() -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.core.config import get_settings
    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    from app.services.auth_service import AuthService

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    today = date.today()
    activated = 0
    errors = 0

    async with SessionLocal() as db:
        repo = PendingEmployeeRepository(db)
        due = await repo.get_pending_due(today)

        for pending in due:
            try:
                svc = AuthService(db)
                employee = await svc.create_employee(
                    email=pending.email,
                    first_name=pending.first_name,
                    last_name=pending.last_name,
                    role=pending.role,
                    manager_id=pending.manager_id,
                    birth_date=pending.birth_date,
                    address=pending.address,
                )
                await repo.delete(pending.id)
                await db.commit()
                activated += 1

                logger.info(
                    "Activated pending employee: %s %s (id=%s) → employee_id=%s",
                    pending.first_name, pending.last_name, pending.id, employee.employee_id,
                )

                # Notify admin via email (fire-and-forget)
                try:
                    from app.tasks.email_tasks import task_send_account_activated_email  # type: ignore
                    task_send_account_activated_email.delay(
                        employee.email,
                        first_name=employee.first_name,
                        last_name=employee.last_name,
                    )
                except Exception:
                    pass

            except Exception as exc:
                logger.error("Failed to activate pending employee id=%s: %s", pending.id, exc)
                errors += 1
                await db.rollback()

    await engine.dispose()
    return {"activated": activated, "errors": errors}


@celery_app.task(name="app.tasks.onboarding_tasks.send_onboarding_reminders")
def send_onboarding_reminders() -> dict:
    """Send J-1 reminder emails to managers for employees arriving tomorrow."""
    return asyncio.get_event_loop().run_until_complete(_send_onboarding_reminders())


async def _send_onboarding_reminders() -> dict:
    """Find pending employees with hire_date == tomorrow and notify their manager."""
    from datetime import timedelta
    from sqlalchemy import select as _select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.core.config import get_settings
    from app.models.pending_employee import PendingEmployee
    from app.models.employee import Employee
    from app.utils.email import send_onboarding_reminder_email

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    tomorrow = date.today() + timedelta(days=1)
    sent = 0
    errors = 0

    async with SessionLocal() as db:
        result = await db.execute(
            _select(PendingEmployee).where(PendingEmployee.hire_date == tomorrow)
        )
        pending_list = result.scalars().all()

        for pending in pending_list:
            try:
                # Récupérer le manager
                manager_first_name = "Manager"
                manager_email: str | None = None

                if pending.manager_id:
                    mgr_result = await db.execute(
                        _select(Employee).where(Employee.employee_id == pending.manager_id)
                    )
                    manager = mgr_result.scalar_one_or_none()
                    if manager:
                        manager_first_name = manager.first_name
                        manager_email = manager.email

                if not manager_email:
                    # Fallback : notifier l'admin (premier admin trouvé)
                    admin_result = await db.execute(
                        _select(Employee).where(
                            Employee.role == "admin",
                            Employee.deleted_at.is_(None),
                        ).limit(1)
                    )
                    admin = admin_result.scalar_one_or_none()
                    if admin:
                        manager_email = admin.email
                        manager_first_name = admin.first_name

                if manager_email:
                    await send_onboarding_reminder_email(
                        to=manager_email,
                        first_name=pending.first_name,
                        last_name=pending.last_name,
                        hire_date=pending.hire_date.strftime("%d/%m/%Y"),
                        manager_first_name=manager_first_name,
                        db=db,
                    )
                    sent += 1
                    logger.info(
                        "J-1 reminder sent for %s %s (hire_date=%s) to %s",
                        pending.first_name, pending.last_name, tomorrow, manager_email,
                    )

            except Exception as exc:
                logger.error("Failed to send J-1 reminder for pending id=%s: %s", pending.id, exc)
                errors += 1

    await engine.dispose()
    return {"sent": sent, "errors": errors}
