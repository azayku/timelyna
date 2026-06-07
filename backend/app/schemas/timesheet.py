"""Pydantic schemas for timesheet endpoints."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class CreateEntryRequest(BaseModel):
    project_id: int
    work_date: date
    hours_worked: Decimal
    description: str
    task_type: str = ""
    entry_type: str = "normal"  # normal | overtime | travel | night
    billable_flag: bool = True
    billing_rate: Optional[Decimal] = None
    notes: Optional[str] = None


class UpdateEntryRequest(BaseModel):
    hours_worked: Optional[Decimal] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    billable_flag: Optional[bool] = None
    billing_rate: Optional[Decimal] = None
    notes: Optional[str] = None


class TimesheetEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timesheet_entry_id: int
    employee_id: int
    project_id: int
    work_date: date
    hours_worked: Decimal
    description: str
    task_type: str
    entry_type: str
    billable_flag: bool
    billing_rate: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    proxy_admin_id: Optional[int] = None


class SubmitWeekRequest(BaseModel):
    week: str


class CreateClientRequest(BaseModel):
    client_name: str
    company_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    default_billing_rate: Decimal
    currency: str = "EUR"
    tax_id: Optional[str] = None


class UpdateClientRequest(BaseModel):
    client_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    default_billing_rate: Optional[Decimal] = None
    currency: Optional[str] = None
    tax_id: Optional[str] = None
    client_status: Optional[str] = None


class ClientResponse(BaseModel):
    client_id: int
    client_name: str
    company_name: Optional[str]
    email: str
    phone: Optional[str]
    address: Optional[str]
    default_billing_rate: Decimal
    currency: str
    tax_id: Optional[str]
    client_status: str

    model_config = {"from_attributes": True}


class CreateProjectRequest(BaseModel):
    client_id: int
    project_name: str
    project_code: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"
    start_date: date
    end_date: Optional[date] = None
    budget_hours: Optional[Decimal] = None
    budget_alert_threshold: Optional[Decimal] = 0.8
    budget_amount: Optional[Decimal] = None
    billing_rate: Decimal
    manager_id: int
    team_members: Optional[list[int]] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"draft", "planning", "active", "paused", "completed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v


class UpdateProjectRequest(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[date] = None
    budget_hours: Optional[Decimal] = None
    budget_alert_threshold: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    billing_rate: Optional[Decimal] = None
    manager_id: Optional[int] = None
    team_members: Optional[list[int]] = None


class ProjectResponse(BaseModel):
    project_id: int
    client_id: int
    project_name: str
    project_code: str
    description: Optional[str] = None
    status: str
    start_date: date
    end_date: Optional[date] = None
    budget_alert_threshold: Optional[Decimal] = None
    budget_hours: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    billing_rate: Decimal
    manager_id: int
    team_members: Optional[list] = None
    client_name: Optional[str] = None
    client_address: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectBudgetStatus(BaseModel):
    """Schema pour l'état du budget d'un projet."""
    project_id: int
    project_name: str
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    budget_hours: Optional[float] = None
    consumed_hours: float
    remaining_hours: Optional[float] = None
    consumption_percentage: Optional[float] = None
    alert: bool  # True si > threshold

    model_config = {"from_attributes": True}
