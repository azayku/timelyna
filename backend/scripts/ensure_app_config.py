from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, "/app")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://timelyna:changeme@postgres:5432/timelyna")


async def ensure_app_config() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with factory() as db:
        await db.execute(text("SELECT pg_advisory_xact_lock(424242)"))
        from app.models.org_settings import OrgSettings

        await db.execute(
            text("ALTER TABLE org_settings ADD COLUMN IF NOT EXISTS next_week_display_day INTEGER NOT NULL DEFAULT 2")
        )

        await db.execute(
            text(
                """
                INSERT INTO org_settings (
                    org_id,
                    standard_hours_per_day,
                    max_hours_per_day,
                    overtime_rate_multiplier,
                    travel_rate_multiplier,
                    default_currency,
                    org_name,
                    account_creation_lead_days,
                    next_week_display_day
                )
                VALUES (1, 8.00, 24.00, 1.25, 0.50, 'EUR', 'Mon Organisation', 2, 2)
                ON CONFLICT (org_id) DO NOTHING
                """
            )
        )

        try:
            from app.models.app_config import AppConfig

            r = await db.execute(select(AppConfig).limit(1))
            if not r.scalar_one_or_none():
                db.add(AppConfig(is_installed=False, app_name="Timelyn"))
                print("app_config row created.")
        except Exception as exc:
            print(f"app_config init skipped: {exc}")

        await db.commit()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(ensure_app_config())