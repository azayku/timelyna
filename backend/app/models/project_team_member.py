"""ProjectTeamMember ORM model."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProjectTeamMember(Base):
    __tablename__ = "project_team_members"
    __table_args__ = (UniqueConstraint("project_id", "employee_id", name="uq_project_team_members"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.project_id"), nullable=False
    )
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.employee_id"), nullable=False
    )
    skill_rate_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("skill_rates.id"), nullable=True
    )
    custom_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
