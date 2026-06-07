"""Organisation settings model."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OrgSettings(Base):
    __tablename__ = "org_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, default=1)

    # Heures journalières
    standard_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("8.00")
    )
    max_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("24.00")
    )

    # Taux heures supplémentaires (multiplicateur, ex: 1.25 = +25%)
    overtime_rate_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("1.25")
    )

    # Taux heures de trajet (multiplicateur, ex: 0.5 = 50%)
    travel_rate_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.50")
    )

    # Devise par défaut
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    # Nom de l'organisation
    org_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Mon Organisation")

    # Spec 12d — deferred account creation lead days
    account_creation_lead_days: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    # Dashboard — jour d'affichage de la semaine prochaine (0=Dimanche, 1=Lundi, 2=Mardi, etc.)
    next_week_display_day: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
