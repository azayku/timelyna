"""Pydantic schemas for multi-org feature (spec 13)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

class CreateOrganizationRequest(BaseModel):
    org_name: str
    manager_id: int


class UpdateOrganizationRequest(BaseModel):
    org_name: Optional[str] = None
    manager_id: Optional[int] = None


class OrganizationResponse(BaseModel):
    org_id: int
    org_name: str
    manager_id: Optional[int] = None
    employee_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Employee Skills
# ---------------------------------------------------------------------------

class AddEmployeeSkillRequest(BaseModel):
    skill_rate_id: int


class EmployeeSkillResponse(BaseModel):
    id: int
    employee_id: int
    skill_rate_id: int
    skill_name: str
    billing_rate: Optional[Decimal] = None
    assigned_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Mutation
# ---------------------------------------------------------------------------

class MutateEmployeeRequest(BaseModel):
    target_org_id: int
    reason: Optional[str] = None

    @field_validator("reason")
    @classmethod
    def reason_max_500(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError("reason must be at most 500 characters")
        return v


class MutationLogResponse(BaseModel):
    id: int
    employee_id: int
    from_org_id: int
    to_org_id: int
    mutated_by: int
    mutated_at: Optional[str] = None
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Project Skills
# ---------------------------------------------------------------------------

class ProjectSkillRequirement(BaseModel):
    skill_rate_id: int
    quantity: int = 1


# ---------------------------------------------------------------------------
# Suggestions
# ---------------------------------------------------------------------------

class SuggestedEmployeeResponse(BaseModel):
    employee_id: int
    full_name: str
    org_name: str
    matching_skills: list[str]
    matching_skill_count: int

    model_config = {"from_attributes": True}
