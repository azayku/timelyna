"""TimesheetEntry ORM model."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

_PK_TYPE = Integer


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"
    __table_args__ = (
        UniqueConstraint("employee_id", "project_id", "work_date", "entry_type",
                         name="uq_employee_project_date_type"),
        Index('ix_timesheet_entry_employee_status_deleted', 'employee_id', 'status', 'deleted_at'),
    )

    timesheet_entry_id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("projects.project_id"), nullable=False
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_worked: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    # entry_type: normal | overtime | travel
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")
    billable_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    billing_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    proxy_admin_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employees.employee_id"), nullable=True
    )
