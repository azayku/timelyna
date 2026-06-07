#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U timesheetpro; do
  sleep 1
done

echo "Running Alembic migrations..."
cd /app/migrations && alembic -c alembic.ini upgrade heads || echo "Alembic upgrade finished (warnings above may be non-fatal)"

echo "Ensuring app_config row exists (setup wizard marker)..."
cd /app && python - <<'EOF'
import asyncio, os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://timesheetpro:changeme@postgres:5432/timesheetpro")

async def ensure_app_config():
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as db:
        from app.models.org_settings import OrgSettings

        # Ensure org_settings row exists (needed by setup wizard)
        r = await db.execute(select(OrgSettings).where(OrgSettings.org_id == 1))
        if not r.scalar_one_or_none():
            db.add(OrgSettings(org_id=1))
            await db.flush()

        # Ensure a single app_config row exists
        try:
            from app.models.app_config import AppConfig
            r = await db.execute(select(AppConfig).limit(1))
            if not r.scalar_one_or_none():
                db.add(AppConfig(is_installed=False, app_name="Timelyn"))
                print("app_config row created.")
        except Exception as e:
            print(f"app_config init skipped: {e}")

        await db.commit()
    await engine.dispose()

asyncio.run(ensure_app_config())
EOF

# If a command was provided (e.g. celery worker/beat from docker-compose), run it.
# Otherwise, start the FastAPI server.
if [ $# -gt 0 ]; then
    echo "Starting $*..."
    cd /app && exec "$@"
else
    echo "Starting FastAPI server..."
    cd /app && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
