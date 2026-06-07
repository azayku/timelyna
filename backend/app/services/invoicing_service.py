"""InvoicingService — business logic for invoice generation."""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.timesheet_entry import TimesheetEntry
from app.repositories.invoicing_repository import InvoicingRepository

logger = logging.getLogger(__name__)


def _parse_invoice_period(period: str) -> tuple[date, date]:
    """Parse period string to (start, end) date range.

    Supports:
    - "2025-03" → month (Mar 2025)
    - "2025-Q1" → quarter (Jan–Mar 2025)
    """
    m = re.match(r'^(\d{4})-(\d{2})$', period)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return start, end

    m = re.match(r'^(\d{4})-Q([1-4])$', period)
    if m:
        year, q = int(m.group(1)), int(m.group(2))
        start_month = (q - 1) * 3 + 1
        start = date(year, start_month, 1)
        end_month = start_month + 2
        if end_month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, end_month + 1, 1) - timedelta(days=1)
        return start, end

    raise ValueError(f"Invalid period: {period}")


class InvoicingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = InvoicingRepository(db)

    # ------------------------------------------------------------------
    # 5.4 — create_draft
    # ------------------------------------------------------------------

    async def create_draft(
        self,
        client_id: int,
        period: str,
        created_by: Optional[int] = None,
        tax_rate: Decimal = Decimal("20.00"),
        currency: str = "EUR",
    ) -> dict:
        try:
            start, end = _parse_invoice_period(period)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        # Collect approved, non-invoiced entries for client in period
        result = await self.db.execute(
            select(TimesheetEntry, Project.billing_rate, Project.project_name, Project.project_id.label("proj_id"))
            .join(Project, TimesheetEntry.project_id == Project.project_id)
            .where(
                Project.client_id == client_id,
                TimesheetEntry.status == "approved",
                TimesheetEntry.deleted_at.is_(None),
                TimesheetEntry.work_date >= start,
                TimesheetEntry.work_date <= end,
            )
        )
        rows = result.all()

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No approved entries for this client and period",
            )

        # Load client default billing rate
        from app.models.client import Client
        client_result = await self.db.execute(
            select(Client).where(Client.client_id == client_id)
        )
        client_obj = client_result.scalar_one_or_none()
        client_default_rate = Decimal(str(client_obj.default_billing_rate)) if client_obj else Decimal("0")

        # Load project team members for rate priority resolution
        from app.models.project_team_member import ProjectTeamMember
        from app.models.skill_rate import SkillRate
        team_result = await self.db.execute(
            select(ProjectTeamMember, SkillRate.billing_rate.label("skill_billing_rate"))
            .outerjoin(SkillRate, ProjectTeamMember.skill_rate_id == SkillRate.id)
            .where(
                ProjectTeamMember.project_id.in_(
                    list({row[0].project_id for row in rows})
                )
            )
        )
        # Build map: (project_id, employee_id) -> (custom_rate, skill_billing_rate)
        team_rate_map: dict[tuple[int, int], tuple] = {}
        for ptm, skill_br in team_result.all():
            team_rate_map[(ptm.project_id, ptm.employee_id)] = (
                ptm.custom_rate,
                skill_br,
            )

        # Group by project → compute line items with priority rates
        projects: dict[int, dict] = {}
        for entry, proj_rate, proj_name, proj_id in rows:
            pid = entry.project_id
            eid = entry.employee_id

            # Priority: custom_rate > skill_rate > project_rate > client_rate
            custom_rate, skill_br = team_rate_map.get((pid, eid), (None, None))
            if custom_rate is not None:
                rate = Decimal(str(custom_rate))
            elif skill_br is not None:
                rate = Decimal(str(skill_br))
            elif proj_rate is not None:
                rate = Decimal(str(proj_rate))
            else:
                rate = client_default_rate

            hours = Decimal(str(entry.hours_worked))
            if pid not in projects:
                projects[pid] = {
                    "project_id": pid,
                    "project_name": proj_name,
                    "hours": Decimal("0"),
                    "rate": float(rate),
                    "subtotal": Decimal("0"),
                }
            projects[pid]["hours"] += hours
            projects[pid]["subtotal"] += hours * rate

        line_items = []
        for item in projects.values():
            line_items.append({
                "project_id": item["project_id"],
                "project_name": item["project_name"],
                "hours": float(item["hours"]),
                "rate": item["rate"],
                "subtotal": float(item["subtotal"]),
            })

        total_hours = sum(Decimal(str(li["hours"])) for li in line_items)
        total_amount = sum(Decimal(str(li["subtotal"])) for li in line_items)
        tax_amount = (total_amount * tax_rate / Decimal("100")).quantize(Decimal("0.01"))

        # Generate FAC-YYYY-NNNN invoice number
        invoice_number = await self.repo.get_next_invoice_number(client_id)

        # Compute subtotal_ht, total_ttc, due_date
        subtotal_ht = total_amount
        total_ttc = total_amount + tax_amount
        due_date = date.today() + timedelta(days=30)

        invoice = await self.repo.create(
            client_id=client_id,
            invoice_number=invoice_number,
            period=period,
            total_hours=total_hours,
            total_amount=total_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            subtotal_ht=subtotal_ht,
            total_ttc=total_ttc,
            due_date=due_date,
            currency=currency,
            line_items=line_items,
            status="draft",
            created_by=created_by,
        )
        await self.db.commit()
        await self.db.refresh(invoice)

        logger.info("Invoice draft created: invoice_id=%s client_id=%s period=%s", invoice.invoice_id, client_id, period)
        return _invoice_to_dict(invoice)

    # ------------------------------------------------------------------
    # 5.5 — finalize
    # ------------------------------------------------------------------

    async def finalize(self, invoice_id: int, performed_by: Optional[int] = None) -> dict:
        invoice = await self.repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

        if invoice.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invoice is already '{invoice.status}', cannot finalize",
            )

        # Parse period to get date range
        start, end = _parse_invoice_period(invoice.period)

        # Get project_ids from line_items
        line_items = invoice.line_items or []
        project_ids = [li["project_id"] for li in line_items]

        # Batch update entries to 'invoiced'
        if project_ids:
            await self.db.execute(
                update(TimesheetEntry)
                .where(
                    TimesheetEntry.project_id.in_(project_ids),
                    TimesheetEntry.status == "approved",
                    TimesheetEntry.deleted_at.is_(None),
                    TimesheetEntry.work_date >= start,
                    TimesheetEntry.work_date <= end,
                )
                .values(status="invoiced")
            )

        invoice = await self.repo.update_status(invoice_id, "ready")
        await self.db.commit()

        # Log audit entry
        await self._log_audit(invoice_id, action="finalized", performed_by=performed_by)
        await self.db.commit()

        logger.info("Invoice finalized: invoice_id=%s", invoice_id)
        return _invoice_to_dict(invoice)

    # ------------------------------------------------------------------
    # 5.6 — send (stub)
    # ------------------------------------------------------------------

    async def send(self, invoice_id: int) -> dict:
        invoice = await self.repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

        if invoice.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invoice must be 'ready' to send (current: '{invoice.status}')",
            )

        now = datetime.now(timezone.utc)
        invoice = await self.repo.update_status(
            invoice_id,
            "sent",
            sent_at=now,
            pdf_s3_url=f"stub://invoices/{invoice_id}.pdf",
        )
        await self.db.commit()

        logger.info("Invoice sent: invoice_id=%s", invoice_id)
        return _invoice_to_dict(invoice)

    # ------------------------------------------------------------------
    # 12a.29 — mark_paid
    # ------------------------------------------------------------------

    async def mark_paid(
        self,
        invoice_id: int,
        paid_at: Optional[datetime] = None,
        performed_by: Optional[int] = None,
    ) -> dict:
        invoice = await self.repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

        if invoice.status not in ("sent", "overdue"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invoice must be 'sent' or 'overdue' to mark as paid (current: '{invoice.status}')",
            )

        paid_at = paid_at or datetime.now(timezone.utc)
        invoice = await self.repo.update_status(invoice_id, "paid", paid_at=paid_at)
        await self.db.commit()

        await self._log_audit(invoice_id, action="paid", performed_by=performed_by, details={"paid_at": paid_at.isoformat()})
        await self.db.commit()

        logger.info("Invoice marked paid: invoice_id=%s", invoice_id)
        return _invoice_to_dict(invoice)

    # ------------------------------------------------------------------
    # Audit log helper
    # ------------------------------------------------------------------

    async def _log_audit(
        self,
        invoice_id: int,
        action: str,
        performed_by: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> None:
        from app.models.invoice_audit_log import InvoiceAuditLog
        log = InvoiceAuditLog(
            invoice_id=invoice_id,
            action=action,
            performed_by=performed_by,
            details=details,
        )
        self.db.add(log)
        await self.db.flush()

    async def get_audit_logs(self, invoice_id: int) -> list[dict]:
        from sqlalchemy import select
        from app.models.invoice_audit_log import InvoiceAuditLog
        result = await self.db.execute(
            select(InvoiceAuditLog)
            .where(InvoiceAuditLog.invoice_id == invoice_id)
            .order_by(InvoiceAuditLog.created_at.asc())
        )
        logs = result.scalars().all()
        return [
            {
                "id": log.id,
                "action": log.action,
                "performed_by": log.performed_by,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def get_by_id(self, invoice_id: int) -> dict:
        invoice = await self.repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        return _invoice_to_dict(invoice)

    async def list_invoices(
        self,
        client_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        invoices = await self.repo.list(client_id=client_id, status=status, skip=skip, limit=limit)
        return [_invoice_to_dict(inv) for inv in invoices]


def _invoice_to_dict(invoice) -> dict:
    return {
        "invoice_id": invoice.invoice_id,
        "client_id": invoice.client_id,
        "invoice_number": invoice.invoice_number,
        "period": invoice.period,
        "total_hours": float(invoice.total_hours) if invoice.total_hours is not None else None,
        "total_amount": float(invoice.total_amount),
        "tax_rate": float(invoice.tax_rate),
        "tax_amount": float(invoice.tax_amount) if invoice.tax_amount is not None else None,
        "subtotal_ht": float(invoice.subtotal_ht) if invoice.subtotal_ht is not None else None,
        "total_ttc": float(invoice.total_ttc) if invoice.total_ttc is not None else None,
        "currency": invoice.currency,
        "line_items": invoice.line_items,
        "status": invoice.status,
        "pdf_s3_url": invoice.pdf_s3_url,
        "due_date": str(invoice.due_date) if invoice.due_date else None,
        "created_by": invoice.created_by,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "sent_at": invoice.sent_at.isoformat() if invoice.sent_at else None,
        "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
    }
