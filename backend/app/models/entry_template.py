"""EntryTemplate ORM model for timesheet entry templates."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

_PK_TYPE = Integer


class EntryTemplate(Base):
    """Template for quick timesheet entry creation."""
    
    __tablename__ = "entry_templates"

    template_id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    org_id: Mapped[int] = mapped_column(_PK_TYPE, nullable=False, server_default="1")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Template name e.g. 'Dev backend sprint'")
    project_id: Mapped[Optional[int]] = mapped_column(
        _PK_TYPE, ForeignKey("projects.project_id"), nullable=True
    )
    task_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    default_hours: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True, server_default="8.0")
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
