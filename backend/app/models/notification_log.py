"""NotificationLog ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

_PK_TYPE = Integer


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    employee_id: Mapped[Optional[int]] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    email_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
