"""Celery export generation tasks."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def run_generate_export(export_id: int, db) -> None:
    """Core async logic: mark export as ready with a stub URL.

    Called directly in tests (passing the test db session).
    In production this is invoked by the Celery task via a fresh session.
    """
    from sqlalchemy import update
    from app.models.export import Export

    await db.execute(
        update(Export)
        .where(Export.id == export_id)
        .values(
            status="ready",
            s3_url=f"stub://exports/{export_id}/report",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )
    await db.commit()


# Celery app is optional — tasks can be called directly in tests
try:
    from celery import Celery
    from app.core.config import get_settings

    _settings = get_settings()
    celery_app = Celery("timelyna", broker=_settings.REDIS_URL)

    @celery_app.task(name="tasks.generate_export")
    def generate_export(export_id: int) -> None:
        """Stub Celery task: in production generates PDF/CSV and uploads to S3."""
        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        from app.core.database import _get_engine  # type: ignore[attr-defined]

        async def _run():
            factory = async_sessionmaker(_get_engine(), expire_on_commit=False, class_=AsyncSession)
            async with factory() as db:
                await run_generate_export(export_id, db)

        asyncio.run(_run())

except Exception:  # noqa: BLE001
    logger.warning("Celery not available — export tasks disabled (use run_generate_export directly)")

    def generate_export(export_id: int) -> None:  # type: ignore[misc]
        logger.info("generate_export stub (no Celery) for export_id=%s", export_id)
