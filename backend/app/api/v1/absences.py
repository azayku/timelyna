"""Absence management API routes."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.absence import Absence
from app.services.absence_service import AbsenceService


# ── Schemas ────────────────────────────────────────────────────────────────

class AbsenceCreateRequest(BaseModel):
    absence_type: str = Field(..., description="Type: cp, maladie, autre")
    start_date: date
    end_date: date
    notes: Optional[str] = None


class AbsenceResponse(BaseModel):
    absence_id: int
    employee_id: int
    employee_name: str
    org_name: str = ""
    absence_type: str
    start_date: date
    end_date: date
    status: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str
    updated_at: str = ""
    # Leave balance info
    annual_leave_days: int = 25
    days_taken_this_year: int = 0
    days_remaining: int = 25
    last_leave_date: Optional[str] = None
    last_leave_days: int = 0

    class Config:
        from_attributes = True


class AbsenceActionRequest(BaseModel):
    reason: Optional[str] = None


# ── Router ─────────────────────────────────────────────────────────────────

router = APIRouter(tags=["absences"])

_manager_role = require_role("manager", "admin")
_admin_role = require_role("admin")


def _uid(user: dict) -> int:
    return int(user.get("employee_id") or user.get("sub") or 0)


def _uname(user: dict) -> str:
    return f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()


def _absence_to_response(a, employee_name: str = "") -> AbsenceResponse:
    return AbsenceResponse(
        absence_id=a.id,
        employee_id=a.employee_id,
        employee_name=employee_name,
        absence_type=a.absence_type,
        start_date=a.start_date,
        end_date=a.end_date,
        status=a.status,
        notes=a.notes,
        rejection_reason=a.rejection_reason,
        created_at=a.created_at.isoformat() if a.created_at else "",
        updated_at=a.updated_at.isoformat() if a.updated_at else "",
    )


# ── Employee Routes ────────────────────────────────────────────────────────

@router.post("/employee/absences", response_model=AbsenceResponse)
async def create_absence(
    req: AbsenceCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AbsenceService(db)
    result = await service.create(
        employee_id=_uid(current_user),
        absence_type=req.absence_type,
        start_date=req.start_date,
        end_date=req.end_date,
        notes=req.notes,
    )
    # service returns a dict — fetch the actual object for consistent response
    from app.repositories.absence_repository import AbsenceRepository
    repo = AbsenceRepository(db)
    absence = await repo.get_by_id(result.get("id") or result.get("absence_id"))
    return _absence_to_response(absence, _uname(current_user))


@router.get("/employee/absences", response_model=List[AbsenceResponse])
async def get_my_absences(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.absence_repository import AbsenceRepository
    repo = AbsenceRepository(db)
    absences = await repo.get_by_employee(_uid(current_user), skip=skip, limit=limit)
    name = _uname(current_user)
    return [_absence_to_response(a, name) for a in absences]


@router.delete("/employee/absences/{absence_id}")
async def cancel_absence(
    absence_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AbsenceService(db)
    # service.cancel(employee_id, absence_id)
    await service.cancel(_uid(current_user), absence_id)
    return {"message": "Absence cancelled successfully"}


# ── Manager Routes ─────────────────────────────────────────────────────────

@router.get("/manager/absences", response_model=List[AbsenceResponse])
async def get_team_absences(
    status: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(_manager_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all absences for employees in organizations managed by the current user.
    Admins see all absences. Managers see only their team's absences.
    """
    from app.models.employee import Employee
    from app.models.organization import Organization
    from datetime import datetime
    
    employee_id = current_user["employee_id"]
    role = current_user.get("role", "")
    
    # Default to current year if not specified
    if year is None:
        year = datetime.now().year
    
    if role == "admin":
        # Admin sees all absences
        stmt = (
            select(Absence, Employee.first_name, Employee.last_name, Employee.annual_leave_days, 
                   Organization.org_name, Employee.org_id)
            .join(Employee, Absence.employee_id == Employee.employee_id)
            .outerjoin(Organization, Employee.org_id == Organization.org_id)
            .where(Employee.deleted_at.is_(None))
        )
    else:
        # Manager sees only absences from their organizations
        # Get organizations managed by current user
        org_stmt = (
            select(Organization.org_id)
            .where(Organization.manager_id == employee_id)
            .where(Organization.deleted_at.is_(None))
        )
        org_result = await db.execute(org_stmt)
        org_ids = [row[0] for row in org_result.all()]
        
        if not org_ids:
            return []
        
        stmt = (
            select(Absence, Employee.first_name, Employee.last_name, Employee.annual_leave_days,
                   Organization.org_name, Employee.org_id)
            .join(Employee, Absence.employee_id == Employee.employee_id)
            .outerjoin(Organization, Employee.org_id == Organization.org_id)
            .where(Employee.org_id.in_(org_ids))
            .where(Employee.deleted_at.is_(None))
        )
    
    if status:
        stmt = stmt.where(Absence.status == status)
    
    # Filter by year
    if year:
        year_start = datetime(year, 1, 1).date()
        year_end = datetime(year, 12, 31).date()
        stmt = stmt.where(
            Absence.start_date <= year_end,
            Absence.end_date >= year_start
        )
    
    stmt = stmt.order_by(Absence.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for absence, first_name, last_name, annual_leave_days, org_name, org_id in rows:
        # Calculate leave balance for this employee
        emp_id = absence.employee_id
        
        # Get all approved CP absences for this year
        year_start = datetime(year, 1, 1).date()
        year_end = datetime(year, 12, 31).date()
        
        cp_stmt = (
            select(Absence)
            .where(Absence.employee_id == emp_id)
            .where(Absence.absence_type == 'cp')
            .where(Absence.status == 'approved')
            .where(Absence.start_date <= year_end)
            .where(Absence.end_date >= year_start)
        )
        cp_result = await db.execute(cp_stmt)
        cp_absences = cp_result.scalars().all()
        
        days_taken = sum((a.end_date - a.start_date).days + 1 for a in cp_absences)
        
        # Get last approved CP absence
        last_cp_stmt = (
            select(Absence)
            .where(Absence.employee_id == emp_id)
            .where(Absence.absence_type == 'cp')
            .where(Absence.status == 'approved')
            .order_by(Absence.end_date.desc())
            .limit(1)
        )
        last_cp_result = await db.execute(last_cp_stmt)
        last_cp = last_cp_result.scalar_one_or_none()
        
        last_leave_date = None
        last_leave_days = 0
        if last_cp:
            last_leave_date = last_cp.end_date.isoformat()
            last_leave_days = (last_cp.end_date - last_cp.start_date).days + 1
        
        response.append(AbsenceResponse(
            absence_id=absence.id,
            employee_id=absence.employee_id,
            employee_name=f"{first_name} {last_name}",
            org_name=org_name or "—",
            absence_type=absence.absence_type,
            start_date=absence.start_date,
            end_date=absence.end_date,
            status=absence.status,
            notes=absence.notes,
            rejection_reason=absence.rejection_reason,
            created_at=absence.created_at.isoformat() if absence.created_at else "",
            updated_at=absence.updated_at.isoformat() if absence.updated_at else "",
            annual_leave_days=annual_leave_days or 25,
            days_taken_this_year=days_taken,
            days_remaining=(annual_leave_days or 25) - days_taken,
            last_leave_date=last_leave_date,
            last_leave_days=last_leave_days,
        ))
    return response


@router.post("/manager/absences/{absence_id}/approve")
async def approve_absence(
    absence_id: int,
    current_user: dict = Depends(_manager_role),
    db: AsyncSession = Depends(get_db),
):
    service = AbsenceService(db)
    # service.approve(manager_id, absence_id)
    await service.approve(_uid(current_user), absence_id)
    return {"message": "Absence approved successfully"}


@router.post("/manager/absences/{absence_id}/reject")
async def reject_absence(
    absence_id: int,
    req: AbsenceActionRequest,
    current_user: dict = Depends(_manager_role),
    db: AsyncSession = Depends(get_db),
):
    service = AbsenceService(db)
    # service.reject(manager_id, absence_id, reason)
    await service.reject(_uid(current_user), absence_id, req.reason or "")
    return {"message": "Absence rejected successfully"}


@router.post("/manager/absences/{absence_id}/revert-to-pending")
async def revert_to_pending(
    absence_id: int,
    current_user: dict = Depends(_manager_role),
    db: AsyncSession = Depends(get_db),
):
    """Revert an approved or rejected absence back to pending status."""
    service = AbsenceService(db)
    await service.revert_to_pending(_uid(current_user), absence_id)
    return {"message": "Absence reverted to pending successfully"}


@router.delete("/manager/absences/{absence_id}")
async def delete_absence(
    absence_id: int,
    current_user: dict = Depends(_manager_role),
    db: AsyncSession = Depends(get_db),
):
    """Delete/cancel an absence (any status)."""
    service = AbsenceService(db)
    await service.delete_by_manager(_uid(current_user), absence_id)
    return {"message": "Absence deleted successfully"}


# ── Admin Routes ───────────────────────────────────────────────────────────

@router.get("/admin/absences", response_model=List[AbsenceResponse])
async def get_all_absences(
    employee_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(_admin_role),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.absence_repository import AbsenceRepository
    from app.repositories.employee_repository import EmployeeRepository

    repo = AbsenceRepository(db)
    emp_repo = EmployeeRepository(db)

    if employee_id:
        absences = await repo.get_by_employee(employee_id)
        if status:
            absences = [a for a in absences if a.status == status]
        if start_date and end_date:
            absences = [a for a in absences if a.start_date <= end_date and a.end_date >= start_date]
    elif start_date and end_date:
        absences = await repo.get_by_date_range(start_date, end_date)
        if status:
            absences = [a for a in absences if a.status == status]
    else:
        absences = await repo.get_all(status=status)

    result = []
    for a in absences:
        emp = await emp_repo.get_by_id(a.employee_id)
        result.append(AbsenceResponse(
            absence_id=a.id,
            employee_id=a.employee_id,
            employee_name=f"{emp.first_name} {emp.last_name}" if emp else "Unknown",
            absence_type=a.absence_type,
            start_date=a.start_date,
            end_date=a.end_date,
            status=a.status,
            notes=a.notes,
            rejection_reason=a.rejection_reason,
            created_at=a.created_at.isoformat() if a.created_at else "",
            updated_at=a.updated_at.isoformat() if a.updated_at else "",
        ))
    return result
