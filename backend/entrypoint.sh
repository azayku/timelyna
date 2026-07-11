#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U timelyna; do
  sleep 1
done

echo "Running Alembic migrations..."
cd /app/migrations
python -m alembic -c alembic.ini upgrade heads || echo "Alembic upgrade finished (warnings above may be non-fatal)"

echo "Ensuring app_config row exists (setup wizard marker)..."
cd /app
python /app/scripts/ensure_app_config.py

if [ "$#" -gt 0 ]; then
  echo "Starting $*..."
  cd /app
  exec "$@"
else
  echo "Starting FastAPI server..."
  cd /app
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
