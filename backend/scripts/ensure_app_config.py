from __future__ import annotations

import asyncio
import os

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://timelyna:changeme@postgres:5432/timelyna")


async def ensure_app_config() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with factory() as db:
        from app.models.org_settings import OrgSettings

        columns_result = await db.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'org_settings'")
        )
        existing_columns = {row[0] for row in columns_result.fetchall()}
        if "next_week_display_day" not in existing_columns:
            await db.execute(
                text("ALTER TABLE org_settings ADD COLUMN next_week_display_day INTEGER NOT NULL DEFAULT 2")
            )
            await db.commit()

        r = await db.execute(select(OrgSettings).where(OrgSettings.org_id == 1))
        if not r.scalar_one_or_none():
            db.add(OrgSettings(org_id=1))
            await db.flush()

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