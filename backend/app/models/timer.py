"""ActiveTimer ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

_PK_TYPE = Integer


class ActiveTimer(Base):
    """Active timer tracking for employees."""
    __tablename__ = "active_timers"

    timer_id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("projects.project_id"), nullable=False
    )
    org_id: Mapped[int] = mapped_column(_PK_TYPE, nullable=False, default=1)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    task_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
