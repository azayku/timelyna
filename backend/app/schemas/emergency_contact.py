"""Pydantic schemas for emergency contacts."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EmergencyContactBase(BaseModel):
    contact_name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., min_length=1, max_length=20)
    contact_type: str = Field(default="urgence")  # urgence, manager, patron, client, autre
    tags: Optional[str] = None  # JSON array as string
    notes: Optional[str] = None


class CreateEmergencyContactRequest(EmergencyContactBase):
    employee_id: int


class UpdateEmergencyContactRequest(BaseModel):
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    contact_type: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EmergencyContactResponse(EmergencyContactBase):
    contact_id: int
    employee_id: int
    created_by: int
    is_active: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
