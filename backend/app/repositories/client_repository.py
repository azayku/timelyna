"""ClientRepository — DB access for clients."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client


class ClientRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, client_id: int) -> Optional[Client]:
        result = await self.db.execute(
            select(Client).where(Client.client_id == client_id, Client.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_active(self, skip: int = 0, limit: int = 20) -> list[Client]:
        result = await self.db.execute(
            select(Client)
            .where(Client.deleted_at.is_(None), Client.client_status == "active")
            .offset(skip)
            .limit(limit)
            .order_by(Client.client_id)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Client:
        client = Client(**kwargs)
        self.db.add(client)
        await self.db.flush()
        await self.db.refresh(client)
        return client

    async def update(self, client_id: int, **kwargs) -> Optional[Client]:
        await self.db.execute(
            update(Client).where(Client.client_id == client_id).values(**kwargs)
        )
        return await self.get_by_id(client_id)

    async def deactivate(self, client_id: int) -> None:
        await self.db.execute(
            update(Client)
            .where(Client.client_id == client_id)
            .values(client_status="inactive")
        )
