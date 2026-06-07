"""Project ORM model."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

_PK_TYPE = Integer


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("clients.client_id"), nullable=False
    )
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    budget_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    budget_alert_threshold: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2), nullable=True, default=0.8, comment="Seuil d'alerte (0.8 = 80%)"
    )
    budget_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    billing_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    manager_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    team_members: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
