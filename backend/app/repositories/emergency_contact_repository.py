"""Repository for emergency contacts."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emergency_contact import EmergencyContact


class EmergencyContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, contact_id: int) -> Optional[EmergencyContact]:
        stmt = select(EmergencyContact).where(EmergencyContact.contact_id == contact_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_employee(self, employee_id: int) -> list[EmergencyContact]:
        """Get all active emergency contacts for an employee."""
        stmt = (
            select(EmergencyContact)
            .where(
                EmergencyContact.employee_id == employee_id,
                EmergencyContact.deleted_at.is_(None),
                EmergencyContact.is_active == True,
            )
            .order_by(EmergencyContact.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_all_active(self) -> list[EmergencyContact]:
        """Get all active emergency contacts across all employees."""
        stmt = select(EmergencyContact).where(
            EmergencyContact.deleted_at.is_(None),
            EmergencyContact.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        employee_id: int,
        contact_name: str,
        phone_number: str,
        contact_type: str,
        created_by: int,
        tags: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> EmergencyContact:
        contact = EmergencyContact(
            employee_id=employee_id,
            contact_name=contact_name,
            phone_number=phone_number,
            contact_type=contact_type,
            created_by=created_by,
            tags=tags,
            notes=notes,
        )
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def update(
        self,
        contact_id: int,
        contact_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        contact_type: Optional[str] = None,
        tags: Optional[str] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[EmergencyContact]:
        contact = await self.get_by_id(contact_id)
        if not contact:
            return None

        if contact_name is not None:
            contact.contact_name = contact_name
        if phone_number is not None:
            contact.phone_number = phone_number
        if contact_type is not None:
            contact.contact_type = contact_type
        if tags is not None:
            contact.tags = tags
        if notes is not None:
            contact.notes = notes
        if is_active is not None:
            contact.is_active = is_active

        await self.db.flush()
        return contact

    async def delete(self, contact_id: int) -> bool:
        """Soft delete an emergency contact."""
        contact = await self.get_by_id(contact_id)
        if not contact:
            return False

        contact.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True
