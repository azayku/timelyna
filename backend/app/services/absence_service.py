"""AbsenceService — business logic for employee absences."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.absence_repository import AbsenceRepository
from app.repositories.employee_repository import EmployeeRepository


class AbsenceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AbsenceRepository(db)
        self.emp_repo = EmployeeRepository(db)

    async def create(
        self,
        employee_id: int,
        absence_type: str,
        start_date: date,
        end_date: date,
        notes: Optional[str] = None,
    ) -> dict:
        """Create a new absence request."""
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date",
            )

        absence = await self.repo.create(
            employee_id=employee_id,
            absence_type=absence_type,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            status="pending",
        )
        await self.db.commit()
        await self.db.refresh(absence)

        # Send notification to manager
        employee = await self.emp_repo.get_by_id(employee_id)
        if employee and employee.manager_id:
            from app.models.notification import Notification
            notif = Notification(
                employee_id=employee.manager_id,
                type="absence_submitted",
                title="Nouvelle demande d'absence",
                message=f"{employee.first_name} {employee.last_name} a soumis une demande d'absence du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
                metadata={"absence_id": absence.id},
            )
            self.db.add(notif)
            await self.db.commit()

        return {
            "id": absence.id,
            "employee_id": absence.employee_id,
            "absence_type": absence.absence_type,
            "start_date": str(absence.start_date),
            "end_date": str(absence.end_date),
            "notes": absence.notes,
            "status": absence.status,
            "created_at": absence.created_at.isoformat() if absence.created_at else None,
        }

    async def approve(self, manager_id: int, absence_id: int) -> dict:
        """Approve an absence request."""
        absence = await self.repo.get_by_id(absence_id)
        if not absence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Absence not found",
            )

        if absence.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve absence with status: {absence.status}",
            )

        # Verify manager has permission (manages employee's organization OR is direct manager)
        employee = await self.emp_repo.get_by_id(absence.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        # Check if manager manages the employee's organization
        from sqlalchemy import select
        from app.models.organization import Organization
        
        org_stmt = select(Organization).where(
            Organization.org_id == employee.org_id,
            Organization.manager_id == manager_id,
            Organization.deleted_at.is_(None)
        )
        org_result = await self.db.execute(org_stmt)
        manages_org = org_result.scalar_one_or_none() is not None

        # Allow if manages organization OR is direct manager
        if not manages_org and employee.manager_id != manager_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to approve this absence",
            )

        absence = await self.repo.update_status(
            absence_id=absence_id,
            status="approved",
            approved_by=manager_id,
        )
        await self.db.commit()

        # Send notification to employee
        notif = Notification(
            employee_id=absence.employee_id,
            type="absence_approved",
            title="Absence approuvée",
            message=f"Votre demande d'absence du {absence.start_date.strftime('%d/%m/%Y')} au {absence.end_date.strftime('%d/%m/%Y')} a été approuvée",
            metadata={"absence_id": absence.id},
        )
        self.db.add(notif)
        await self.db.commit()

        return {
            "id": absence.id,
            "status": absence.status,
            "approved_by": absence.approved_by,
            "approved_at": absence.approved_at.isoformat() if absence.approved_at else None,
        }

    async def reject(self, manager_id: int, absence_id: int, reason: str) -> dict:
        """Reject an absence request."""
        absence = await self.repo.get_by_id(absence_id)
        if not absence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Absence not found",
            )

        if absence.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject absence with status: {absence.status}",
            )

        # Verify manager has permission (manages employee's organization OR is direct manager)
        employee = await self.emp_repo.get_by_id(absence.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        # Check if manager manages the employee's organization
        from sqlalchemy import select
        from app.models.organization import Organization
        
        org_stmt = select(Organization).where(
            Organization.org_id == employee.org_id,
            Organization.manager_id == manager_id,
            Organization.deleted_at.is_(None)
        )
        org_result = await self.db.execute(org_stmt)
        manages_org = org_result.scalar_one_or_none() is not None

        # Allow if manages organization OR is direct manager
        if not manages_org and employee.manager_id != manager_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to reject this absence",
            )

        absence = await self.repo.update_status(
            absence_id=absence_id,
            status="rejected",
            approved_by=manager_id,
            rejection_reason=reason,
        )
        await self.db.commit()

        # Send notification to employee
        notif = Notification(
            employee_id=absence.employee_id,
            type="absence_rejected",
            title="Absence refusée",
            message=f"Votre demande d'absence du {absence.start_date.strftime('%d/%m/%Y')} au {absence.end_date.strftime('%d/%m/%Y')} a été refusée. Raison: {reason or 'Non spécifiée'}",
            metadata={"absence_id": absence.id, "reason": reason},
        )
        self.db.add(notif)
        await self.db.commit()

        return {
            "id": absence.id,
            "status": absence.status,
            "rejection_reason": absence.rejection_reason,
        }

    async def revert_to_pending(self, manager_id: int, absence_id: int) -> dict:
        """Revert an approved or rejected absence back to pending status."""
        absence = await self.repo.get_by_id(absence_id)
        if not absence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Absence not found",
            )

        if absence.status == "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Absence is already pending",
            )

        # Verify manager has permission
        employee = await self.emp_repo.get_by_id(absence.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        # Check if manager manages the employee's organization
        from sqlalchemy import select
        from app.models.organization import Organization
        
        org_stmt = select(Organization).where(
            Organization.org_id == employee.org_id,
            Organization.manager_id == manager_id,
            Organization.deleted_at.is_(None)
        )
        org_result = await self.db.execute(org_stmt)
        manages_org = org_result.scalar_one_or_none() is not None

        # Allow if manages organization OR is direct manager
        if not manages_org and employee.manager_id != manager_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to modify this absence",
            )

        # Revert to pending
        absence = await self.repo.update_status(
            absence_id=absence_id,
            status="pending",
            approved_by=None,
            rejection_reason=None,
        )
        await self.db.commit()

        # Send notification to employee
        notif = Notification(
            employee_id=absence.employee_id,
            type="absence_reverted",
            title="Absence remise en attente",
            message=f"Votre demande d'absence du {absence.start_date.strftime('%d/%m/%Y')} au {absence.end_date.strftime('%d/%m/%Y')} a été remise en attente",
            metadata={"absence_id": absence.id},
        )
        self.db.add(notif)
        await self.db.commit()

        return {
            "id": absence.id,
            "status": absence.status,
        }

    async def delete_by_manager(self, manager_id: int, absence_id: int) -> None:
        """Delete an absence (manager can delete any absence from their team)."""
        absence = await self.repo.get_by_id(absence_id)
        if not absence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Absence not found",
            )

        # Verify manager has permission
        employee = await self.emp_repo.get_by_id(absence.employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        # Check if manager manages the employee's organization
        from sqlalchemy import select
        from app.models.organization import Organization
        
        org_stmt = select(Organization).where(
            Organization.org_id == employee.org_id,
            Organization.manager_id == manager_id,
            Organization.deleted_at.is_(None)
        )
        org_result = await self.db.execute(org_stmt)
        manages_org = org_result.scalar_one_or_none() is not None

        # Allow if manages organization OR is direct manager
        if not manages_org and employee.manager_id != manager_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this absence",
            )

        await self.db.delete(absence)
        await self.db.commit()

    async def cancel(self, employee_id: int, absence_id: int) -> None:
        """Cancel a pending absence request."""
        absence = await self.repo.get_by_id(absence_id)
        if not absence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Absence not found",
            )

        if absence.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own absences",
            )

        if absence.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel pending absences",
            )

        await self.db.delete(absence)
        await self.db.commit()

    async def get_leave_balance(self, employee_id: int, year: int) -> dict:
        """Calculate leave balance for an employee."""
        employee = await self.emp_repo.get_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        annual_leave_days = employee.annual_leave_days or 25

        # Get approved absences for the year
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        absences = await self.repo.get_by_date_range([employee_id], start_date, end_date)

        # Count days taken (only 'cp' type)
        days_taken = 0
        for absence in absences:
            if absence.absence_type == "cp":
                delta = (absence.end_date - absence.start_date).days + 1
                days_taken += delta

        return {
            "employee_id": employee_id,
            "year": year,
            "annual_leave_days": annual_leave_days,
            "days_taken": days_taken,
            "days_remaining": annual_leave_days - days_taken,
        }
