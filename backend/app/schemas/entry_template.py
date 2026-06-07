"""Pydantic schemas for entry templates."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EntryTemplateCreate(BaseModel):
    """Schema for creating a new entry template."""
    
    name: str = Field(..., max_length=100, description="Template name")
    project_id: Optional[int] = Field(None, description="Project ID")
    task_type: Optional[str] = Field(None, max_length=100, description="Task type")
    description: Optional[str] = Field(None, max_length=500, description="Default description")
    default_hours: Optional[float] = Field(8.0, ge=0, le=24, description="Default hours")
    is_favorite: bool = Field(False, description="Mark as favorite")


class EntryTemplateUpdate(BaseModel):
    """Schema for updating an existing entry template."""
    
    name: Optional[str] = Field(None, max_length=100, description="Template name")
    project_id: Optional[int] = Field(None, description="Project ID")
    task_type: Optional[str] = Field(None, max_length=100, description="Task type")
    description: Optional[str] = Field(None, max_length=500, description="Default description")
    default_hours: Optional[float] = Field(None, ge=0, le=24, description="Default hours")
    is_favorite: Optional[bool] = Field(None, description="Mark as favorite")


class EntryTemplateResponse(BaseModel):
    """Schema for entry template response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    template_id: int
    employee_id: int
    org_id: int
    name: str
    project_id: Optional[int]
    task_type: Optional[str]
    description: Optional[str]
    default_hours: Optional[float]
    is_favorite: bool
    created_at: datetime
    updated_at: Optional[datetime]
