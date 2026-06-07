"""ApprovalRepository — DB access for approval records."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval
from app.models.employee import Employee
from app.models.timesheet_entry import TimesheetEntry


class ApprovalRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, approval_id: int) -> Optional[Approval]:
        result = await self.db.execute(
            select(Approval).where(Approval.approval_id == approval_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_for_manager(
        self, manager_id: int, skip: int = 0, limit: int = 20
    ) -> list[Approval]:
        """Return pending approvals for employees who report to manager_id."""
        result = await self.db.execute(
            select(Approval)
            .join(Employee, Employee.employee_id == Approval.employee_id)
            .where(
                Employee.manager_id == manager_id,
                Approval.status == "pending",
            )
            .offset(skip)
            .limit(limit)
            .order_by(Approval.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_employee(
        self,
        employee_id: int,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Approval]:
        q = select(Approval).where(Approval.employee_id == employee_id)
        if status_filter and status_filter != "all":
            q = q.where(Approval.status == status_filter)
        q = q.offset(skip).limit(limit).order_by(Approval.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_all(
        self,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Approval]:
        q = select(Approval)
        if status_filter and status_filter != "all":
            q = q.where(Approval.status == status_filter)
        q = q.offset(skip).limit(limit).order_by(Approval.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_all_with_details(
        self,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """Return approvals with employee names and total hours."""
        # Build base query
        q = (
            select(
                Approval,
                Employee.first_name,
                Employee.last_name,
            )
            .join(Employee, Employee.employee_id == Approval.employee_id)
        )
        
        if status_filter and status_filter != "all":
            q = q.where(Approval.status == status_filter)
        
        q = q.offset(skip).limit(limit).order_by(Approval.created_at.desc())
        result = await self.db.execute(q)
        rows = result.all()
        
        # For each approval, calculate total hours
        enriched = []
        for approval, first_name, last_name in rows:
            week_end = approval.week_start + timedelta(days=6)
            
            # Sum hours for this week
            hours_result = await self.db.execute(
                select(func.sum(TimesheetEntry.hours_worked))
                .where(
                    TimesheetEntry.employee_id == approval.employee_id,
                    TimesheetEntry.work_date >= approval.week_start,
                    TimesheetEntry.work_date <= week_end,
                    TimesheetEntry.deleted_at.is_(None),
                )
            )
            total_hours = hours_result.scalar() or 0.0
            
            enriched.append({
                "approval": approval,
                "employee_name": f"{first_name} {last_name}",
                "total_hours": float(total_hours),
            })
        
        return enriched

    async def update_status(
        self,
        approval_id: int,
        status: str,
        decided_by: Optional[int] = None,
        notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> Optional[Approval]:
        approval = await self.get_by_id(approval_id)
        if not approval:
            return None
        approval.status = status
        approval.decided_at = datetime.now(timezone.utc)
        if decided_by is not None:
            approval.manager_id = decided_by
        if notes is not None:
            approval.notes = notes
        if rejection_reason is not None:
            approval.rejection_reason = rejection_reason
        await self.db.flush()
        await self.db.refresh(approval)
        return approval
