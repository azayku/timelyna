"""ProjectRequiredSkill ORM model."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# SQLite doesn't support BigInteger autoincrement via RETURNING; use Integer for PK.
_PK_TYPE = Integer


class ProjectRequiredSkill(Base):
    __tablename__ = "project_required_skills"
    __table_args__ = (
        UniqueConstraint("project_id", "skill_rate_id", name="uq_project_required_skills"),
    )

    id: Mapped[int] = mapped_column(_PK_TYPE, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("projects.project_id"), nullable=False
    )
    skill_rate_id: Mapped[int] = mapped_column(
        _PK_TYPE, ForeignKey("skill_rates.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
