"""AppConfig ORM model — global application configuration (single row)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AppConfig(Base):
    """Single-row table that stores the app installation state and branding."""

    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Installation flag — False until the setup wizard is completed
    is_installed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Branding
    app_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Timelyn")
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Logo stored as base64 data-URL (small image) or a path/URL
    company_logo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    installed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
