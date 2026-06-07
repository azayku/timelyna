"""EmployeeSkill ORM model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# SQLite doesn't support BigInteger autoincrement via RETURNING; use Integer for PK.
_PK_TYPE = Integer


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    __table_args__ = (UniqueConstraint("employee_id", "skill_rate_id", name="uq_employee_skills"),)

    id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    skill_rate_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("skill_rates.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
