"""InvoicingRepository — DB access for invoices."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice


class InvoicingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> Invoice:
        invoice = Invoice(**kwargs)
        self.db.add(invoice)
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.invoice_id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        client_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Invoice]:
        q = select(Invoice)
        if client_id is not None:
            q = q.where(Invoice.client_id == client_id)
        if status is not None:
            q = q.where(Invoice.status == status)
        q = q.offset(skip).limit(limit).order_by(Invoice.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def update_status(self, invoice_id: int, status: str, **extra_fields) -> Optional[Invoice]:
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            return None
        invoice.status = status
        for key, value in extra_fields.items():
            setattr(invoice, key, value)
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def get_next_invoice_number(self, client_id: int) -> str:
        """Generate globally unique invoice number like FAC-2025-0042."""
        from datetime import datetime, timezone
        year = datetime.now(timezone.utc).year
        result = await self.db.execute(select(func.count(Invoice.invoice_id)))
        count = result.scalar_one() or 0
        seq = count + 1
        return f"FAC-{year}-{seq:04d}"
