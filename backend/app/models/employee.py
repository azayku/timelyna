"""Employee ORM model."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# SQLite doesn't support BIGINT autoincrement via RETURNING; use Integer for PK
# In production (PostgreSQL), BigInteger is used via the FK references
_PK_TYPE = Integer


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="employee")
    employment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    manager_id: Mapped[Optional[int]] = mapped_column(
        _PK_TYPE, ForeignKey("employees.employee_id"), nullable=True
    )
    # org_id is a FK to organizations.org_id — no SQLAlchemy FK declared here to avoid circular imports
    org_id: Mapped[int] = mapped_column(_PK_TYPE, nullable=False, default=1)
    # Extended fields for spec 02
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hourly_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Spec 11 — username & password management
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Spec 12c — address & deferred deactivation
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    deactivation_scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    annual_leave_days: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    # Spec 12b — preferred language for emails/UI
    preferred_language: Mapped[str] = mapped_column(String(5), nullable=False, default='fr')
    # MFA/2FA fields
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="Secret TOTP pour 2FA")
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="2FA activé")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        "RefreshToken", back_populates="employee", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(  # noqa: F821
        "PasswordResetToken", back_populates="employee", cascade="all, delete-orphan"
    )
