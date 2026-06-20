"""Async SQLAlchemy engine and session factory."""
from __future__ import annotations

import socket
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine = None
_AsyncSessionLocal = None


def _build_connect_args() -> dict:
    """Build connect_args based on the DATABASE_URL dialect."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("postgresql"):
        # Check if SSL should be disabled (for local Docker)
        if "ssl=disable" in url.lower() or "sslmode=disable" in url.lower():
            return {
                "ssl": False,
                "server_settings": {"application_name": "timelyna"},
            }
        # Force SSL for production (Supabase, etc.)
        return {
            "ssl": "require",
            "server_settings": {"application_name": "timelyna"},
        }
    return {}


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = _build_connect_args()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def _get_session_factory():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            _get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_session_factory()
    async with factory() as session:
        yield session


# Export session maker for scripts
async_session_maker = _get_session_factory
