"""EmployeeMutationLog ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# SQLite doesn't support BigInteger autoincrement via RETURNING; use Integer for PK.
_PK_TYPE = Integer


class EmployeeMutationLog(Base):
    __tablename__ = "employee_mutation_logs"

    id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    from_org_id: Mapped[int] = mapped_column(_PK_TYPE, nullable=False)
    to_org_id: Mapped[int] = mapped_column(_PK_TYPE, nullable=False)
    mutated_by: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    mutated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
