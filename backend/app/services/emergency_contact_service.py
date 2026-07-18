"""Service for managing emergency contacts."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.emergency_contact_repository import EmergencyContactRepository
from app.schemas.emergency_contact import (
    CreateEmergencyContactRequest,
    EmergencyContactResponse,
    UpdateEmergencyContactRequest,
)


class EmergencyContactService:
    def __init__(self, db: AsyncSession):
        self.repo = EmergencyContactRepository(db)

    async def get_contact(self, contact_id: int) -> Optional[EmergencyContactResponse]:
        contact = await self.repo.get_by_id(contact_id)
        if not contact:
            return None
        return EmergencyContactResponse.model_validate(contact)

    async def get_employee_contacts(self, employee_id: int) -> list[EmergencyContactResponse]:
        contacts = await self.repo.get_by_employee(employee_id)
        return [EmergencyContactResponse.model_validate(c) for c in contacts]

    async def get_all_contacts(self) -> list[EmergencyContactResponse]:
        contacts = await self.repo.get_all_active()
        return [EmergencyContactResponse.model_validate(c) for c in contacts]

    async def create_contact(
        self, payload: CreateEmergencyContactRequest, created_by: int
    ) -> EmergencyContactResponse:
        contact = await self.repo.create(
            employee_id=payload.employee_id,
            contact_name=payload.contact_name,
            phone_number=payload.phone_number,
            contact_type=payload.contact_type,
            created_by=created_by,
            tags=payload.tags,
            notes=payload.notes,
        )
        return EmergencyContactResponse.model_validate(contact)

    async def update_contact(
        self, contact_id: int, payload: UpdateEmergencyContactRequest
    ) -> Optional[EmergencyContactResponse]:
        contact = await self.repo.update(
            contact_id=contact_id,
            contact_name=payload.contact_name,
            phone_number=payload.phone_number,
            contact_type=payload.contact_type,
            tags=payload.tags,
            notes=payload.notes,
            is_active=payload.is_active,
        )
        if not contact:
            return None
        return EmergencyContactResponse.model_validate(contact)

    async def delete_contact(self, contact_id: int) -> bool:
        return await self.repo.delete(contact_id)
