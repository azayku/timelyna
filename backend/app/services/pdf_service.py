"""Service de génération PDF pour les exports."""
from __future__ import annotations

import logging
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


class PDFService:
    """Service de génération de PDF pour les rapports de timesheet."""

    def generate_timesheet_pdf(
        self,
        employee_name: str,
        org_name: str,
        entries: list[dict],
        period_start: date,
        period_end: date,
    ) -> bytes:
        """Génère un PDF de rapport de timesheet.

        Args:
            employee_name: Nom complet de l'employé
            org_name: Nom de l'organisation
            entries: Liste des entrées timesheet avec work_date, project_name, task_type, hours_worked, description, status
            period_start: Date de début de période
            period_end: Date de fin de période

        Returns:
            bytes: Contenu du PDF généré
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=4,
            alignment=TA_CENTER,
            textColor=colors.grey,
        )

        story = []

        # En-tête du rapport
        story.append(Paragraph("Rapport de Timesheet", title_style))
        story.append(Paragraph(f"{employee_name} — {org_name}", subtitle_style))
        story.append(
            Paragraph(
                f"Période : {period_start.strftime('%d/%m/%Y')} au {period_end.strftime('%d/%m/%Y')}",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 10 * mm))

        # Tableau des entrées
        headers = ["Date", "Projet", "Type", "Heures", "Description", "Statut"]
        data = [headers]

        total_hours = 0.0
        for entry in entries:
            work_date = entry.get("work_date", "")
            if hasattr(work_date, "strftime"):
                work_date = work_date.strftime("%d/%m/%Y")
            hours = entry.get("hours_worked", 0)
            total_hours += float(hours)
            data.append(
                [
                    str(work_date),
                    str(entry.get("project_name", entry.get("project_id", ""))),
                    str(entry.get("task_type", "")),
                    f"{hours:.1f}h",
                    str(entry.get("description", ""))[:60],
                    str(entry.get("status", "")),
                ]
            )

        # Ligne de total
        data.append(["", "", "TOTAL", f"{total_hours:.1f}h", "", ""])

        col_widths = [25 * mm, 40 * mm, 25 * mm, 18 * mm, 55 * mm, 22 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (3, 0), (3, -1), "CENTER"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -2),
                        [colors.white, colors.HexColor("#f8fafc")],
                    ),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e7ff")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_hours_report_pdf(
        self,
        org_name: str,
        entries: list[dict],
        period_start: date,
        period_end: date,
    ) -> bytes:
        """Génère un PDF du rapport d'heures (admin/manager) avec colonne employé."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=4,
            alignment=TA_CENTER,
            textColor=colors.grey,
        )

        story = []
        story.append(Paragraph("Rapport d'Heures", title_style))
        story.append(Paragraph(org_name, subtitle_style))
        story.append(
            Paragraph(
                f"Période : {period_start.strftime('%d/%m/%Y')} au {period_end.strftime('%d/%m/%Y')}",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 10 * mm))

        headers = ["Date", "Employé", "Projet", "Type", "Heures", "Statut"]
        data = [headers]

        total_hours = 0.0
        for entry in entries:
            work_date = entry.get("work_date", "")
            if hasattr(work_date, "strftime"):
                work_date = work_date.strftime("%d/%m/%Y")
            hours = entry.get("hours_worked", 0)
            total_hours += float(hours)
            data.append(
                [
                    str(work_date),
                    str(entry.get("employee_name", ""))[:25],
                    str(entry.get("project_name", ""))[:25],
                    str(entry.get("task_type", "")),
                    f"{float(hours):.1f}h",
                    str(entry.get("status", "")),
                ]
            )

        data.append(["", "", "", "TOTAL", f"{total_hours:.1f}h", ""])

        col_widths = [22 * mm, 40 * mm, 40 * mm, 22 * mm, 18 * mm, 22 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (4, 0), (4, -1), "CENTER"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -2),
                        [colors.white, colors.HexColor("#f8fafc")],
                    ),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e7ff")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
