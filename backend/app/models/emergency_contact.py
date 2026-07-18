"""Emergency contact ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

_PK_TYPE = Integer


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    contact_id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="urgence"
    )  # urgence, manager, patron, client, autre
    tags: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array stored as text
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Integer, nullable=False, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
