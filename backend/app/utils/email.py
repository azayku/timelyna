"""Email sending utilities — logs in dev, sends via SMTP in production."""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Send email. In dev (no SMTP_HOST configured) just logs — no connection attempt."""
    settings = get_settings()

    # Skip SMTP only if no host is configured or explicitly set to localhost (no server running)
    if not settings.SMTP_HOST or settings.SMTP_HOST == "localhost":
        logger.info("[DEV EMAIL] To: %s | Subject: %s", to, subject)
        return

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(settings.EMAIL_FROM, [to], msg.as_string())
        logger.info("Email sent to %s: %s", to, subject)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to send email to %s: %s", to, exc)


async def send_password_reset_email(
    to: str, 
    reset_link: str, 
    first_name: str = "", 
    last_name: str = "",
    db: Optional[AsyncSession] = None,
    template_name: str = "password_reset",
) -> None:
    """Send password reset email. Checks DB for custom template first."""
    subject = "Réinitialisation de votre mot de passe Timelyna"
    body = f"Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe (valable 1 heure) :\n\n{reset_link}\n"
    
    if db:
        try:
            from app.services.email_template_service import EmailTemplateService
            template_service = EmailTemplateService(db)
            settings = get_settings()
            org_name = getattr(settings, 'ORG_NAME', 'Timelyna')
            context = {
                "first_name": first_name,
                "last_name": last_name,
                "reset_link": reset_link,
                "org_name": org_name,
            }
            subject, body = await template_service.render_template(template_name, context)
        except Exception as exc:
            logger.debug("Could not load custom template '%s', using default: %s", template_name, exc)
    
    send_email(to=to, subject=subject, body=body)


def send_password_changed_email(to: str, lang: str = "fr") -> None:
    """Send password changed notification email."""
    subjects = {
        "fr": "Votre mot de passe Timelyna a été modifié",
        "en": "Your Timelyna password has been changed",
        "it": "La tua password Timelyna è stata modificata",
    }
    bodies = {
        "fr": "Votre mot de passe a été modifié avec succès. Si vous n'êtes pas à l'origine de cette action, contactez le support.",
        "en": "Your password has been successfully changed. If you did not initiate this action, please contact support.",
        "it": "La tua password è stata modificata con successo. Se non hai eseguito questa azione, contatta il supporto.",
    }
    resolved = lang if lang in subjects else "fr"
    send_email(to=to, subject=subjects[resolved], body=bodies[resolved])


async def send_welcome_email(
    to: str, 
    setup_link: str, 
    first_name: str = "", 
    last_name: str = "",
    username: str = "",
    db: Optional[AsyncSession] = None,
    template_name: str = "welcome_new_employee",
) -> None:
    """Send welcome email to new employee. Checks DB for custom template first."""
    subject = "Bienvenue sur Timelyna"
    body = f"Votre compte a été créé. Configurez votre mot de passe ici (lien valable 24h) :\n\n{setup_link}\n"
    
    if db:
        try:
            from app.services.email_template_service import EmailTemplateService
            template_service = EmailTemplateService(db)
            settings = get_settings()
            org_name = getattr(settings, 'ORG_NAME', 'Timelyna')
            context = {
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "setup_link": setup_link,
                "org_name": org_name,
            }
            subject, body = await template_service.render_template(template_name, context)
        except Exception as exc:
            logger.debug("Could not load custom template '%s', using default: %s", template_name, exc)

    send_email(to=to, subject=subject, body=body)


async def send_onboarding_reminder_email(
    to: str,
    first_name: str,
    last_name: str,
    hire_date: str,
    manager_first_name: str,
    db: Optional[AsyncSession] = None,
    template_name: str = "onboarding_reminder",
) -> None:
    """Send J-1 reminder email to manager about new employee arriving tomorrow."""
    subject = f"Rappel : {first_name} {last_name} arrive demain"
    body = (
        f"Bonjour {manager_first_name},\n\n"
        f"{first_name} {last_name} rejoint votre équipe demain ({hire_date}).\n"
        f"Son compte Timelyna sera activé ce soir.\n\n"
        "Cordialement,\nTimelyna"
    )

    if db:
        try:
            from app.services.email_template_service import EmailTemplateService
            template_service = EmailTemplateService(db)
            settings = get_settings()
            org_name = getattr(settings, 'ORG_NAME', 'Timelyna')
            context = {
                "first_name": first_name,
                "last_name": last_name,
                "hire_date": hire_date,
                "manager_first_name": manager_first_name,
                "org_name": org_name,
            }
            subject, body = await template_service.render_template(template_name, context)
        except Exception as exc:
            logger.debug("Could not load custom template '%s', using default: %s", template_name, exc)

    send_email(to=to, subject=subject, body=body)


async def send_budget_alert_email(
    to: str,
    project_name: str,
    consumption_pct: float,
    budget_hours: float,
    consumed_hours: float,
    remaining_hours: float,
    manager_first_name: str,
    db: Optional[AsyncSession] = None,
    template_name: str = "budget_alert",
) -> None:
    """Send budget alert email to project manager when threshold exceeded."""
    subject = f"⚠️ Alerte budget — {project_name} ({consumption_pct:.0f}%)"
    body = (
        f"Bonjour {manager_first_name},\n\n"
        f"Le projet {project_name} a atteint {consumption_pct:.0f}% de son budget.\n"
        f"Budget : {budget_hours:.0f}h | Consommé : {consumed_hours:.1f}h | Restant : {remaining_hours:.1f}h\n\n"
        "Cordialement,\nTimelyna"
    )

    if db:
        try:
            from app.services.email_template_service import EmailTemplateService
            template_service = EmailTemplateService(db)
            settings = get_settings()
            org_name = getattr(settings, 'ORG_NAME', 'Timelyna')
            context = {
                "project_name": project_name,
                "consumption_pct": f"{consumption_pct:.0f}",
                "budget_hours": f"{budget_hours:.0f}",
                "consumed_hours": f"{consumed_hours:.1f}",
                "remaining_hours": f"{remaining_hours:.1f}",
                "manager_first_name": manager_first_name,
                "org_name": org_name,
            }
            subject, body = await template_service.render_template(template_name, context)
        except Exception as exc:
            logger.debug("Could not load custom template '%s', using default: %s", template_name, exc)

    send_email(to=to, subject=subject, body=body)
