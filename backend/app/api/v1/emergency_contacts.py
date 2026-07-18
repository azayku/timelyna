"""Emergency contacts management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.emergency_contact import (
    CreateEmergencyContactRequest,
    EmergencyContactResponse,
    UpdateEmergencyContactRequest,
)
from app.services.emergency_contact_service import EmergencyContactService

router = APIRouter(prefix="/emergency-contacts", tags=["emergency-contacts"])


@router.get("", response_model=list[EmergencyContactResponse])
async def list_all_contacts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all emergency contacts. Accessible to admins and managers."""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    svc = EmergencyContactService(db)
    return await svc.get_all_contacts()


@router.get("/employee/{employee_id}", response_model=list[EmergencyContactResponse])
async def list_employee_contacts(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get emergency contacts for a specific employee."""
    # Managers can see their team's contacts, employees can see their own
    if current_user["role"] == "employee" and current_user["employee_id"] != employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    svc = EmergencyContactService(db)
    return await svc.get_employee_contacts(employee_id)


@router.post("", response_model=EmergencyContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: CreateEmergencyContactRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an emergency contact. Admins can create for anyone, managers for their team."""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    svc = EmergencyContactService(db)
    return await svc.create_contact(payload, created_by=current_user["employee_id"])


@router.put("/{contact_id}", response_model=EmergencyContactResponse)
async def update_contact(
    contact_id: int,
    payload: UpdateEmergencyContactRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an emergency contact. Admins can update any, managers can update their team's."""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    svc = EmergencyContactService(db)
    contact = await svc.update_contact(contact_id, payload)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an emergency contact. Admins only."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    svc = EmergencyContactService(db)
    success = await svc.delete_contact(contact_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return None
