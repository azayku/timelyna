"""ApprovalService — business logic for approval workflow."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timesheet_entry import TimesheetEntry
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.tasks.notification_tasks import task_send_approval_notification  # noqa: E402

logger = logging.getLogger(__name__)


class ApprovalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ApprovalRepository(db)
        self.emp_repo = EmployeeRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def _resolve_manager_id(self, employee_id: int) -> int:
        """Resolve manager_id via organizations.manager_id from employees.org_id.

        Returns the manager_id of the employee's organization.
        Raises 422 with code 'no_valid_organization' if the employee has no valid org.
        """
        employee = await self.emp_repo.get_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )
        org = await self.org_repo.get_by_id(employee.org_id)
        if not org or org.manager_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "detail": "Employee has no valid organization or organization has no manager",
                    "code": "no_valid_organization",
                },
            )
        return org.manager_id

    # ------------------------------------------------------------------
    # 3.4 — approve
    # ------------------------------------------------------------------

    async def approve(
        self,
        approver_id: int,
        approval_id: int,
        notes: Optional[str] = None,
        is_admin: bool = False,
    ) -> dict:
        approval = await self.repo.get_by_id(approval_id)
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

        if not is_admin:
            # Resolve manager via org hierarchy instead of employees.manager_id directly
            org_manager_id = await self._resolve_manager_id(approval.employee_id)
            if org_manager_id != approver_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not the manager of this employee",
                )

        if approval.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Approval is already '{approval.status}', cannot approve",
            )

        before_status = approval.status
        now = datetime.now(timezone.utc)

        # Update approval record
        await self.repo.update_status(
            approval_id,
            status="approved",
            decided_by=approver_id,
            notes=notes,
        )

        # Batch update entries
        week_end = approval.week_start + timedelta(days=6)
        await self.db.execute(
            update(TimesheetEntry)
            .where(
                TimesheetEntry.employee_id == approval.employee_id,
                TimesheetEntry.work_date >= approval.week_start,
                TimesheetEntry.work_date <= week_end,
                TimesheetEntry.status == "submitted",
                TimesheetEntry.deleted_at.is_(None),
            )
            .values(status="approved", approved_at=now)
        )

        await self.db.commit()

        # Audit log (3.10)
        logger.info(
            "AUDIT approve: user_id=%s approval_id=%s action=approve before=%s after=approved",
            approver_id, approval_id, before_status,
        )

        # Notification (10.6)
        try:
            from app.tasks.notification_tasks import run_create_in_app_notification
            await run_create_in_app_notification(
                employee_id=approval.employee_id,
                type="approval_approved",
                title="Timesheet approved",
                message=f"Your timesheet for week {approval.week_start} has been approved.",
                entity_type="approval",
                entity_id=approval.approval_id,
                db=self.db,
            )
            await self.db.commit()
        except Exception:
            logger.warning("Approval notification failed", exc_info=True)

        # Email notification in employee's preferred language (US-6)
        try:
            employee = await self.emp_repo.get_by_id(approval.employee_id)
            lang = employee.preferred_language if employee else "fr"
            task_send_approval_notification(
                employee_id=approval.employee_id,
                approval_id=approval_id,
                status="approved",
                week_start=str(approval.week_start),
                lang=lang,
            )
        except Exception:
            logger.warning(
                "Could not send approval email notification for approval_id=%s (non-blocking)",
                approval_id,
            )

        return {"approval_id": approval_id, "status": "approved"}

    # ------------------------------------------------------------------
    # 3.5 — reject
    # ------------------------------------------------------------------

    async def reject(
        self,
        approver_id: int,
        approval_id: int,
        rejection_reason: str,
        is_admin: bool = False,
    ) -> dict:
        approval = await self.repo.get_by_id(approval_id)
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

        if not is_admin:
            # Resolve manager via org hierarchy instead of employees.manager_id directly
            org_manager_id = await self._resolve_manager_id(approval.employee_id)
            if org_manager_id != approver_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not the manager of this employee",
                )

        if approval.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Approval is already '{approval.status}', cannot reject",
            )

        if len(rejection_reason.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="rejection_reason must be at least 10 characters",
            )

        before_status = approval.status

        # Update approval record
        await self.repo.update_status(
            approval_id,
            status="rejected",
            decided_by=approver_id,
            rejection_reason=rejection_reason,
        )

        # Reset entries back to draft
        week_end = approval.week_start + timedelta(days=6)
        await self.db.execute(
            update(TimesheetEntry)
            .where(
                TimesheetEntry.employee_id == approval.employee_id,
                TimesheetEntry.work_date >= approval.week_start,
                TimesheetEntry.work_date <= week_end,
                TimesheetEntry.status == "submitted",
                TimesheetEntry.deleted_at.is_(None),
            )
            .values(status="draft", approved_at=None)
        )

        await self.db.commit()

        # Audit log (3.10)
        logger.info(
            "AUDIT reject: user_id=%s approval_id=%s action=reject before=%s after=rejected reason=%s",
            approver_id, approval_id, before_status, rejection_reason,
        )

        # Notification (10.6)
        try:
            from app.tasks.notification_tasks import run_create_in_app_notification
            await run_create_in_app_notification(
                employee_id=approval.employee_id,
                type="approval_rejected",
                title="Timesheet rejected",
                message=f"Your timesheet for week {approval.week_start} was rejected: {rejection_reason}",
                entity_type="approval",
                entity_id=approval.approval_id,
                db=self.db,
            )
            await self.db.commit()
        except Exception:
            logger.warning("Approval rejection notification failed", exc_info=True)

        # Email notification in employee's preferred language (US-6)
        try:
            employee = await self.emp_repo.get_by_id(approval.employee_id)
            lang = employee.preferred_language if employee else "fr"
            task_send_approval_notification(
                employee_id=approval.employee_id,
                approval_id=approval_id,
                status="rejected",
                week_start=str(approval.week_start),
                lang=lang,
            )
        except Exception:
            logger.warning(
                "Could not send rejection email notification for approval_id=%s (non-blocking)",
                approval_id,
            )

        return {"approval_id": approval_id, "status": "rejected"}

    # ------------------------------------------------------------------
    # 3.6 — cancel
    # ------------------------------------------------------------------

    async def cancel(self, employee_id: int, approval_id: int) -> dict:
        approval = await self.repo.get_by_id(approval_id)
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

        if approval.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this submission",
            )

        if approval.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only pending submissions can be cancelled (current: '{approval.status}')",
            )

        before_status = approval.status

        await self.repo.update_status(approval_id, status="cancelled")

        # Reset entries back to draft
        week_end = approval.week_start + timedelta(days=6)
        await self.db.execute(
            update(TimesheetEntry)
            .where(
                TimesheetEntry.employee_id == approval.employee_id,
                TimesheetEntry.work_date >= approval.week_start,
                TimesheetEntry.work_date <= week_end,
                TimesheetEntry.status == "submitted",
                TimesheetEntry.deleted_at.is_(None),
            )
            .values(status="draft", approved_at=None)
        )

        await self.db.commit()

        # Audit log (3.10)
        logger.info(
            "AUDIT cancel: user_id=%s approval_id=%s action=cancel before=%s after=cancelled",
            employee_id, approval_id, before_status,
        )

        return {"approval_id": approval_id, "status": "cancelled"}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def get_pending_for_manager(
        self, manager_id: int, page: int = 1, page_size: int = 20
    ) -> list[dict]:
        skip = (page - 1) * page_size
        approvals = await self.repo.get_pending_for_manager(manager_id, skip, page_size)
        return [_approval_to_dict(a) for a in approvals]

    async def get_by_id_for_manager(
        self, manager_id: int, approval_id: int, is_admin: bool = False
    ) -> dict:
        approval = await self.repo.get_by_id(approval_id)
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
        if not is_admin:
            # Resolve manager via org hierarchy
            org_manager_id = await self._resolve_manager_id(approval.employee_id)
            if org_manager_id != manager_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not the manager of this employee",
                )
        return _approval_to_dict(approval)

    async def get_by_employee(
        self,
        employee_id: int,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict]:
        skip = (page - 1) * page_size
        approvals = await self.repo.get_by_employee(employee_id, status_filter, skip, page_size)
        return [_approval_to_dict(a) for a in approvals]

    async def get_all_admin(
        self,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict]:
        skip = (page - 1) * page_size
        enriched = await self.repo.get_all_with_details(status_filter, skip, page_size)

        result = []
        for item in enriched:
            approval = item["approval"]
            result.append({
                "approval_id": approval.approval_id,
                "employee_id": approval.employee_id,
                "employee_name": item["employee_name"],
                "manager_id": approval.manager_id,
                "week_start": str(approval.week_start),
                "total_hours": item["total_hours"],
                "status": approval.status,
                "notes": approval.notes,
                "rejection_reason": approval.rejection_reason,
                "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
                "created_at": approval.created_at.isoformat() if approval.created_at else None,
                "updated_at": approval.updated_at.isoformat() if approval.updated_at else None,
            })

        return result


def _approval_to_dict(approval) -> dict:
    return {
        "approval_id": approval.approval_id,
        "employee_id": approval.employee_id,
        "manager_id": approval.manager_id,
        "week_start": str(approval.week_start),
        "status": approval.status,
        "notes": approval.notes,
        "rejection_reason": approval.rejection_reason,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "updated_at": approval.updated_at.isoformat() if approval.updated_at else None,
    }
