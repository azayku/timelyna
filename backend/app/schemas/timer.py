"""Timer request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TimerStart(BaseModel):
    """Request to start a timer."""
    project_id: int = Field(..., description="ID du projet à chronométrer")
    description: Optional[str] = Field(None, max_length=500, description="Description de la tâche")
    task_type: Optional[str] = Field(None, max_length=100, description="Type de tâche")


class TimerResponse(BaseModel):
    """Active timer information."""
    model_config = ConfigDict(from_attributes=True)

    timer_id: int
    employee_id: int
    project_id: int
    description: Optional[str]
    task_type: Optional[str]
    started_at: datetime
    elapsed_seconds: Optional[int] = None  # calculé dynamiquement, pas en DB


class TimerStopResponse(BaseModel):
    """Response after stopping a timer."""
    message: str
    hours_worked: float
    timesheet_entry_id: Optional[int] = None
