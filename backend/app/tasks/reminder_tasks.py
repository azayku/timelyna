"""
Celery tasks for timesheet reminders.
"""
from datetime import date, timedelta
from typing import List

from celery import shared_task
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import _get_session_factory
from app.models.employee import Employee
from app.models.timesheet_entry import TimesheetEntry
from app.models.absence import Absence
from app.models.notification_preference import NotificationPreference
from app.models.notification_log import NotificationLog
from app.utils.email import send_email


async def _get_employees_with_missing_timesheets(
    db: AsyncSession, start_date: date, end_date: date
) -> List[Employee]:
    """
    Get employees who have missing timesheet entries for the given period.
    Excludes employees who were absent for the entire period.
    """
    # Get all active employees
    result = await db.execute(
        select(Employee).where(
            and_(
                Employee.employment_status == "active",
                Employee.deleted_at.is_(None)
            )
        )
    )
    employees = result.scalars().all()
    
    employees_with_missing = []
    
    for emp in employees:
        # Check if employee has any timesheet entries for the period
        entries_result = await db.execute(
            select(TimesheetEntry).where(
                and_(
                    TimesheetEntry.employee_id == emp.employee_id,
                    TimesheetEntry.work_date >= start_date,
                    TimesheetEntry.work_date <= end_date,
                    TimesheetEntry.deleted_at.is_(None)
                )
            )
        )
        entries = entries_result.scalars().all()
        
        # Check if employee was absent for the entire period
        absences_result = await db.execute(
            select(Absence).where(
                and_(
                    Absence.employee_id == emp.employee_id,
                    Absence.status == "approved",
                    Absence.start_date <= start_date,
                    Absence.end_date >= end_date
                )
            )
        )
        full_period_absence = absences_result.scalar_one_or_none()
        
        # If no entries and not absent for entire period, add to list
        if not entries and not full_period_absence:
            # Check notification preferences
            pref_result = await db.execute(
                select(NotificationPreference).where(
                    and_(
                        NotificationPreference.employee_id == emp.employee_id,
                        NotificationPreference.type == "timesheet_reminder"
                    )
                )
            )
            pref = pref_result.scalar_one_or_none()
            
            # If no preference exists, default to enabled
            # If preference exists, check if email is enabled
            if not pref or pref.email_enabled:
                employees_with_missing.append(emp)
    
    return employees_with_missing


@shared_task(name="send_weekly_timesheet_reminders")
def send_weekly_timesheet_reminders():
    """
    Send weekly timesheet reminders to employees who haven't logged hours
    for the previous week. Runs every Monday at 4 PM.
    """
    import asyncio
    
    async def _send_reminders():
        session_factory = _get_session_factory()
        async with session_factory() as db:
            # Calculate previous week (Monday to Sunday)
            today = date.today()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            
            employees = await _get_employees_with_missing_timesheets(
                db, last_monday, last_sunday
            )
            
            sent_count = 0
            for emp in employees:
                try:
                    # Send email
                    await send_email(
                        to_email=emp.email,
                        subject="Rappel : Saisie des heures manquante",
                        template_name="timesheet_reminder",
                        context={
                            "employee_name": f"{emp.first_name} {emp.last_name}",
                            "period_start": last_monday.strftime("%d/%m/%Y"),
                            "period_end": last_sunday.strftime("%d/%m/%Y"),
                            "period_type": "semaine",
                        }
                    )
                    
                    # Log notification
                    log = NotificationLog(
                        employee_id=emp.employee_id,
                        type="timesheet_reminder",
                        channel="email",
                        status="sent",
                        metadata={
                            "period_start": last_monday.isoformat(),
                            "period_end": last_sunday.isoformat(),
                            "reminder_type": "weekly"
                        }
                    )
                    db.add(log)
                    sent_count += 1
                    
                except Exception as e:
                    # Log failed notification
                    log = NotificationLog(
                        employee_id=emp.employee_id,
                        type="timesheet_reminder",
                        channel="email",
                        status="failed",
                        metadata={
                            "period_start": last_monday.isoformat(),
                            "period_end": last_sunday.isoformat(),
                            "reminder_type": "weekly",
                            "error": str(e)
                        }
                    )
                    db.add(log)
            
            await db.commit()
            return sent_count
    
    result = asyncio.run(_send_reminders())
    return f"Sent {result} weekly timesheet reminders"


@shared_task(name="send_monthly_timesheet_reminders")
def send_monthly_timesheet_reminders():
    """
    Send monthly timesheet reminders for any unsubmitted weeks in the previous month.
    Runs on the last day of each month at 12 PM.
    """
    import asyncio
    
    async def _send_reminders():
        session_factory = _get_session_factory()
        async with session_factory() as db:
            # Calculate previous month
            today = date.today()
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            
            employees = await _get_employees_with_missing_timesheets(
                db, last_month_start, last_month_end
            )
            
            sent_count = 0
            for emp in employees:
                try:
                    # Send email
                    await send_email(
                        to_email=emp.email,
                        subject="Rappel mensuel : Saisie des heures manquante",
                        template_name="timesheet_reminder",
                        context={
                            "employee_name": f"{emp.first_name} {emp.last_name}",
                            "period_start": last_month_start.strftime("%d/%m/%Y"),
                            "period_end": last_month_end.strftime("%d/%m/%Y"),
                            "period_type": "mois",
                        }
                    )
                    
                    # Log notification
                    log = NotificationLog(
                        employee_id=emp.employee_id,
                        type="timesheet_reminder",
                        channel="email",
                        status="sent",
                        metadata={
                            "period_start": last_month_start.isoformat(),
                            "period_end": last_month_end.isoformat(),
                            "reminder_type": "monthly"
                        }
                    )
                    db.add(log)
                    sent_count += 1
                    
                except Exception as e:
                    # Log failed notification
                    log = NotificationLog(
                        employee_id=emp.employee_id,
                        type="timesheet_reminder",
                        channel="email",
                        status="failed",
                        metadata={
                            "period_start": last_month_start.isoformat(),
                            "period_end": last_month_end.isoformat(),
                            "reminder_type": "monthly",
                            "error": str(e)
                        }
                    )
                    db.add(log)
            
            await db.commit()
            return sent_count
    
    result = asyncio.run(_send_reminders())
    return f"Sent {result} monthly timesheet reminders"
