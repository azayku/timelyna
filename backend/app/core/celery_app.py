"""Celery application factory with Beat schedule."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()

    app = Celery(
        "timesheetpro",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=[
            "app.tasks.email_tasks",
            "app.tasks.export_tasks",
            "app.tasks.invoice_tasks",
            "app.tasks.notification_tasks",
            "app.tasks.deactivation_tasks",
            "app.tasks.reminder_tasks",
            "app.tasks.onboarding_tasks",
            "app.tasks.budget_tasks",
        ],
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        beat_schedule={
            "process-scheduled-deactivations": {
                "task": "app.tasks.deactivation_tasks.process_scheduled_deactivations",
                "schedule": crontab(hour=0, minute=5),
            },
            "mark-overdue-invoices": {
                "task": "app.tasks.invoice_tasks.mark_overdue_invoices",
                "schedule": crontab(hour=1, minute=0),
            },
            "send-weekly-timesheet-reminders": {
                "task": "send_weekly_timesheet_reminders",
                "schedule": crontab(day_of_week=1, hour=16, minute=0),
            },
            "send-monthly-timesheet-reminders": {
                "task": "send_monthly_timesheet_reminders",
                "schedule": crontab(day_of_month=28, hour=12, minute=0),
            },
            "activate-pending-employees": {
                "task": "app.tasks.onboarding_tasks.activate_pending_employees",
                "schedule": crontab(hour=7, minute=0),
            },
            "send-onboarding-reminders": {
                "task": "app.tasks.onboarding_tasks.send_onboarding_reminders",
                "schedule": crontab(hour=17, minute=0),  # J-1 @ 17h00
            },
            "send-budget-alerts": {
                "task": "app.tasks.budget_tasks.send_budget_alerts",
                "schedule": crontab(hour=9, minute=0),  # tous les jours @ 09h00
            },
        },
    )

    return app


# Module-level singleton — import this in task modules
celery_app = create_celery_app()


celery_app = create_celery_app()
