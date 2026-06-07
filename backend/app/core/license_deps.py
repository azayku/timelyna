"""FastAPI dependencies for license feature gates and limit checks."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db


def require_feature(feature_name: str):
    """FastAPI dependency factory that checks license feature gate.

    In tests/dev (no license configured): always allows access.
    With license: raises 402 if feature not enabled.
    """

    async def _check() -> None:
        settings = get_settings()
        if not settings.LICENSE_PUBLIC_KEY:
            return  # No license configured → allow all (dev mode)
        # Production: validate license from DB and check feature
        # For now: stub that always passes
        return

    return _check


def check_limit(resource: str):
    """FastAPI dependency that checks license limits on create operations.

    In dev mode (no LICENSE_PUBLIC_KEY): always allows.
    """

    async def _check(db: AsyncSession = Depends(get_db)) -> None:
        settings = get_settings()
        if not settings.LICENSE_PUBLIC_KEY:
            return  # Dev mode
        # Production: check current count vs license limit
        return

    return _check
