"""EmailTemplateService — manage and render email templates."""
from __future__ import annotations

import logging
import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES: dict[str, dict] = {
    "welcome_new_employee": {
        "subject": "Bienvenue sur Timelyna — {{org_name}}",
        "html_body": (
            "<p>Bonjour {{first_name}},<br>"
            "Votre compte a été créé. Identifiant : <strong>{{username}}</strong><br>"
            "<a href='{{setup_link}}'>Définir mon mot de passe</a></p>"
        ),
        "variables": ["first_name", "last_name", "username", "setup_link", "org_name"],
    },
    "password_reset": {
        "subject": "Réinitialisation de mot de passe — {{org_name}}",
        "html_body": (
            "<p>Bonjour {{first_name}},<br>"
            "Vous avez demandé la réinitialisation de votre mot de passe.<br><br>"
            "<a href='{{reset_link}}' style='background:#6366f1;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;'>Réinitialiser mon mot de passe</a>"
            "<br><br>Ce lien est valable <strong>1 heure</strong>.<br>"
            "Si vous n'avez pas fait cette demande, ignorez cet email.</p>"
        ),
        "variables": ["first_name", "last_name", "reset_link", "org_name"],
    },
    "onboarding_reminder": {
        "subject": "🎉 Bienvenue demain chez {{org_name}} — {{first_name}} {{last_name}}",
        "html_body": (
            "<p>Bonjour {{manager_first_name}},</p>"
            "<p>Rappel : <strong>{{first_name}} {{last_name}}</strong> rejoint votre équipe "
            "demain (<strong>{{hire_date}}</strong>).</p>"
            "<p>Son compte Timelyna sera automatiquement activé ce soir. "
            "Il/elle recevra un email de bienvenue avec ses identifiants.</p>"
            "<p>Cordialement,<br>Timelyna</p>"
        ),
        "variables": ["first_name", "last_name", "hire_date", "manager_first_name", "org_name"],
    },
    "budget_alert": {
        "subject": "⚠️ Alerte budget — {{project_name}} ({{consumption_pct}}%)",
        "html_body": (
            "<p>Bonjour {{manager_first_name}},</p>"
            "<p>Le projet <strong>{{project_name}}</strong> a atteint "
            "<strong>{{consumption_pct}}%</strong> de son budget alloué.</p>"
            "<table style='border-collapse:collapse;width:100%;max-width:400px'>"
            "<tr><td style='padding:6px;border:1px solid #e2e8f0'>Budget total</td>"
            "<td style='padding:6px;border:1px solid #e2e8f0'><strong>{{budget_hours}}h</strong></td></tr>"
            "<tr><td style='padding:6px;border:1px solid #e2e8f0'>Consommé</td>"
            "<td style='padding:6px;border:1px solid #e2e8f0'><strong>{{consumed_hours}}h</strong></td></tr>"
            "<tr><td style='padding:6px;border:1px solid #e2e8f0'>Restant</td>"
            "<td style='padding:6px;border:1px solid #e2e8f0'><strong>{{remaining_hours}}h</strong></td></tr>"
            "</table>"
            "<p>Veuillez vérifier l'avancement et ajuster si nécessaire.</p>"
            "<p>Cordialement,<br>Timelyna</p>"
        ),
        "variables": [
            "project_name", "consumption_pct", "budget_hours",
            "consumed_hours", "remaining_hours", "manager_first_name", "org_name",
        ],
    },
}


class EmailTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_template(self, key: str) -> dict:
        """Return template from DB if customised, else return default."""
        try:
            from app.models.email_template import EmailTemplate
            result = await self.db.execute(
                select(EmailTemplate).where(EmailTemplate.template_key == key)
            )
            tmpl = result.scalar_one_or_none()
            if tmpl:
                return {
                    "key": tmpl.template_key,
                    "subject": tmpl.subject,
                    "html_body": tmpl.html_body,
                    "text_body": tmpl.text_body,
                    "is_custom": True,
                    "updated_at": tmpl.updated_at.isoformat() if tmpl.updated_at else None,
                }
        except Exception:
            logger.warning("Email template load failed", exc_info=True)

        default = DEFAULT_TEMPLATES.get(key)
        if not default:
            raise ValueError(f"Unknown template key: {key}")
        return {
            "key": key,
            "subject": default["subject"],
            "html_body": default["html_body"],
            "text_body": None,
            "is_custom": False,
            "updated_at": None,
        }

    async def list_templates(self) -> list[dict]:
        """Return all known templates with their current state."""
        templates = []
        for key in DEFAULT_TEMPLATES:
            tmpl = await self.get_template(key)
            templates.append(tmpl)
        return templates

    async def render_template(self, key: str, context: dict) -> tuple[str, str]:
        """Render template with context variables. Returns (subject, html_body)."""
        tmpl = await self.get_template(key)
        subject = self._replace_vars(tmpl["subject"], context)
        html_body = self._replace_vars(tmpl["html_body"], context)
        return subject, html_body

    async def update_template(
        self, key: str, subject: str, html_body: str, updated_by: int
    ) -> dict:
        """Create or update a custom template in DB."""
        if key not in DEFAULT_TEMPLATES:
            raise ValueError(f"Unknown template key: {key}")

        from app.models.email_template import EmailTemplate
        from datetime import datetime, timezone

        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.template_key == key)
        )
        tmpl = result.scalar_one_or_none()
        if tmpl:
            tmpl.subject = subject
            tmpl.html_body = html_body
            tmpl.updated_by = updated_by
            tmpl.updated_at = datetime.now(timezone.utc)
        else:
            tmpl = EmailTemplate(
                template_key=key,
                subject=subject,
                html_body=html_body,
                updated_by=updated_by,
            )
            self.db.add(tmpl)
        await self.db.flush()
        await self.db.refresh(tmpl)
        await self.db.commit()
        return await self.get_template(key)

    async def reset_to_default(self, key: str) -> None:
        """Delete custom template from DB, reverting to default."""
        if key not in DEFAULT_TEMPLATES:
            raise ValueError(f"Unknown template key: {key}")
        try:
            from app.models.email_template import EmailTemplate
            result = await self.db.execute(
                select(EmailTemplate).where(EmailTemplate.template_key == key)
            )
            tmpl = result.scalar_one_or_none()
            if tmpl:
                await self.db.delete(tmpl)
                await self.db.commit()
        except Exception:
            logger.warning("Email template reset failed", exc_info=True)

    @staticmethod
    def _replace_vars(text: str, context: dict) -> str:
        """Replace {{var}} placeholders with context values."""
        def replacer(match: re.Match) -> str:
            var = match.group(1).strip()
            return str(context.get(var, match.group(0)))
        return re.sub(r"\{\{(\w+)\}\}", replacer, text)
