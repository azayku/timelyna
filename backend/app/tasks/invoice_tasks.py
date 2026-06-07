"""Celery invoice generation tasks."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def run_generate_invoice_pdf(invoice_id: int, db) -> None:
    """Core async logic: stub PDF generation — sets pdf_s3_url on the invoice."""
    from sqlalchemy import update
    from app.models.invoice import Invoice

    await db.execute(
        update(Invoice)
        .where(Invoice.invoice_id == invoice_id)
        .values(pdf_s3_url=f"stub://invoices/{invoice_id}.pdf")
    )
    await db.commit()
    logger.info("Invoice PDF generated (stub): invoice_id=%s", invoice_id)


async def run_mark_overdue_invoices(db) -> int:
    """Core async logic: mark sent invoices with due_date < today as overdue."""
    from datetime import date
    from sqlalchemy import update, select
    from app.models.invoice import Invoice

    today = date.today()
    result = await db.execute(
        update(Invoice)
        .where(
            Invoice.status == "sent",
            Invoice.due_date.isnot(None),
            Invoice.due_date < today,
        )
        .values(status="overdue")
        .returning(Invoice.invoice_id)
    )
    updated_ids = result.fetchall()
    await db.commit()
    count = len(updated_ids)
    logger.info("Marked %d invoices as overdue", count)
    return count


import asyncio as _asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.celery_app import celery_app
from app.core.database import _get_engine  # type: ignore[attr-defined]


@celery_app.task(name="tasks.generate_invoice_pdf")
def generate_invoice_pdf(invoice_id: int) -> None:
    """Celery task: generate PDF for an invoice (stub — sets pdf_s3_url)."""
    async def _run():
        factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
        async with factory() as db:
            await run_generate_invoice_pdf(invoice_id, db)

    _asyncio.run(_run())


@celery_app.task(name="app.tasks.invoice_tasks.mark_overdue_invoices")
def mark_overdue_invoices() -> None:
    """Daily task: mark sent invoices with due_date < today as overdue."""
    async def _run():
        factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
        async with factory() as db:
            await run_mark_overdue_invoices(db)

    _asyncio.run(_run())
