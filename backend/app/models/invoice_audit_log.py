"""InvoiceAuditLog ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvoiceAuditLog(Base):
    __tablename__ = "invoice_audit_logs"

    # Use Integer (not BigInteger) for SQLite compatibility in tests
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("invoices.invoice_id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    performed_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("employees.employee_id"), nullable=True
    )
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
