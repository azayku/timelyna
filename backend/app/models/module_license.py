"""Module license model for modular licensing system."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModuleLicense(Base):
    __tablename__ = "module_licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    license_key: Mapped[str] = mapped_column(String(100), nullable=False)
    expires_at: Mapped[date] = mapped_column(Date, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("org_id", "module_name", name="uq_org_module"),
    )
