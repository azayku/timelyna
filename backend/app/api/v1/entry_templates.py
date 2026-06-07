"""Entry templates routes — /api/v1/entry-templates/..."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.entry_template import EntryTemplate
from app.schemas.entry_template import (
    EntryTemplateCreate,
    EntryTemplateResponse,
    EntryTemplateUpdate,
)

router = APIRouter(prefix="/entry-templates", tags=["Entry Templates"])


@router.get("/", response_model=list[EntryTemplateResponse])
async def get_my_templates(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EntryTemplate]:
    """Get all templates for the current user (favorites first)."""
    result = await db.execute(
        select(EntryTemplate)
        .where(EntryTemplate.employee_id == current_user["employee_id"])
        .order_by(EntryTemplate.is_favorite.desc(), EntryTemplate.name)
    )
    return list(result.scalars().all())


@router.post("/", response_model=EntryTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: EntryTemplateCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryTemplate:
    """Create a new entry template (max 20 per employee)."""
    # Check template count limit
    count_result = await db.execute(
        select(func.count()).select_from(EntryTemplate).where(
            EntryTemplate.employee_id == current_user["employee_id"]
        )
    )
    count = count_result.scalar()
    
    if count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum de 20 templates par utilisateur atteint",
        )
    
    # Create template
    template = EntryTemplate(
        employee_id=current_user["employee_id"],
        org_id=current_user.get("org_id", 1),
        **payload.model_dump(),
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.get("/{template_id}", response_model=EntryTemplateResponse)
async def get_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryTemplate:
    """Get a specific template by ID."""
    result = await db.execute(
        select(EntryTemplate).where(
            EntryTemplate.template_id == template_id,
            EntryTemplate.employee_id == current_user["employee_id"],
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template non trouvé",
        )
    
    return template


@router.put("/{template_id}", response_model=EntryTemplateResponse)
async def update_template(
    template_id: int,
    payload: EntryTemplateUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryTemplate:
    """Update an existing entry template."""
    result = await db.execute(
        select(EntryTemplate).where(
            EntryTemplate.template_id == template_id,
            EntryTemplate.employee_id == current_user["employee_id"],
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template non trouvé",
        )
    
    # Update fields
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template)
    
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete an entry template."""
    result = await db.execute(
        select(EntryTemplate).where(
            EntryTemplate.template_id == template_id,
            EntryTemplate.employee_id == current_user["employee_id"],
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template non trouvé",
        )
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "Template supprimé avec succès"}
