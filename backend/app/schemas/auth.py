"""Pydantic schemas for auth endpoints."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*\d).{8,}$")


class LoginRequest(BaseModel):
    identifier: str  # Email or username
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError(
                "Password must be at least 8 characters with 1 uppercase letter and 1 digit"
            )
        return v


class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetBody(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError(
                "Password must be at least 8 characters with 1 uppercase letter and 1 digit"
            )
        return v


class CreateUserRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str  # employee | manager | admin | finance | payroll
    manager_id: Optional[int] = None
    birth_date: date          # obligatoire
    address: str              # obligatoire
    hire_date: Optional[date] = None  # 12d.25 — deferred onboarding


class UserResponse(BaseModel):
    employee_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    employment_status: str
    manager_id: Optional[int]
    org_id: int
    username: Optional[str] = None
    must_change_password: bool = False
    address: Optional[str] = None
    birth_date: Optional[date] = None
    deactivation_scheduled_at: Optional[datetime] = None
    preferred_language: str = 'fr'
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    employment_status: Optional[str] = None
    manager_id: Optional[int] = None
    address: Optional[str] = None
    birth_date: Optional[date] = None
