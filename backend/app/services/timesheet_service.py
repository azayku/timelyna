"""TimesheetService — business logic for timesheet operations."""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_settings import OrgSettings
from app.models.timesheet_entry import TimesheetEntry
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.timesheet_repository import TimesheetRepository

logger = logging.getLogger(__name__)


def parse_iso_week(week_str: str) -> tuple[date, date]:
    """Parse '2025-W12' → (monday, sunday)."""
    m = re.match(r"^(\d{4})-W(\d{1,2})$", week_str)
    if not m:
        raise ValueError(f"Invalid week format: {week_str}")
    year, week = int(m.group(1)), int(m.group(2))
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


class TimesheetService:
    def __init__(self, db: AsyncSession, org_id: int = 1) -> None:
        self.db = db
        self.org_id = org_id
        self.repo = TimesheetRepository(db)
        self.emp_repo = EmployeeRepository(db)
        self.proj_repo = ProjectRepository(db)

    async def _load_org_settings(self) -> OrgSettings | None:
        """Load OrgSettings for the current organization."""
        result = await self.db.execute(
            select(OrgSettings).where(OrgSettings.org_id == self.org_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # 2.10 — get_week
    # ------------------------------------------------------------------

    async def get_week(self, employee_id: int, week_str: str) -> dict:
        try:
            start_date, end_date = parse_iso_week(week_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid week format. Use YYYY-Www (e.g. 2025-W12)",
            )

        entries = await self.repo.get_week(employee_id, start_date, end_date)

        # Group by work_date
        by_date: dict[str, list[dict]] = {}
        daily_totals: dict[str, float] = {}

        for entry in entries:
            d = str(entry.work_date)
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(_entry_to_dict(entry))
            daily_totals[d] = float(daily_totals.get(d, 0)) + float(entry.hours_worked)

        week_total = sum(daily_totals.values())

        return {
            "week": week_str,
            "entries": by_date,
            "daily_totals": daily_totals,
            "week_total": week_total,
        }

    # ------------------------------------------------------------------
    # 2.11 — create_entry
    # ------------------------------------------------------------------

    async def create_entry(self, employee_id: int, data: dict, proxy_admin_id: int | None = None) -> dict:
        hours = Decimal(str(data["hours_worked"]))
        work_date: date = data["work_date"]
        if isinstance(work_date, str):
            work_date = date.fromisoformat(work_date)

        # Validate hours range (min 0.25, max from org settings)
        if hours < Decimal("0.25"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le nombre d'heures doit être au moins 0.25",
            )

        # Load org settings for max hours
        org_settings = await self._load_org_settings()
        max_hours = Decimal(str(org_settings.max_hours_per_day)) if org_settings else Decimal("24")

        if hours > max_hours:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Le nombre d'heures ne peut pas dépasser {max_hours}h par jour",
            )

        # Validate work_date not in future
        if work_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La date de saisie ne peut pas être dans le futur",
            )

        # Check project exists and is active
        project = await self.proj_repo.get_by_id(data["project_id"])
        if not project or project.status != "active":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Projet introuvable ou non actif",
            )

        # Check unique (employee, project, date, entry_type)
        entry_type = data.get("entry_type", "normal")
        existing = await self.db.execute(
            select(TimesheetEntry).where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.project_id == data["project_id"],
                TimesheetEntry.work_date == work_date,
                TimesheetEntry.entry_type == entry_type,
                TimesheetEntry.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une saisie existe déjà pour cet employé, ce projet, cette date et ce type",
            )

        # Check daily total ≤ max_hours (only for normal entries)
        if entry_type == "normal":
            daily_total = await self.repo.get_daily_total(employee_id, work_date)
            if Decimal(str(daily_total)) + hours > max_hours:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Le total des heures normales pour cette journée dépasserait {max_hours}h",
                )

        entry = await self.repo.create(
            employee_id=employee_id,
            project_id=data["project_id"],
            work_date=work_date,
            hours_worked=hours,
            description=data["description"],
            task_type=data.get("task_type", ""),
            entry_type=entry_type,
            billable_flag=data.get("billable_flag", True),
            billing_rate=data.get("billing_rate"),
            notes=data.get("notes"),
            status="draft",
            proxy_admin_id=proxy_admin_id,
        )
        await self.db.commit()
        await self.db.refresh(entry)
        return _entry_to_dict(entry)

    # ------------------------------------------------------------------
    # 2.12 — update_entry
    # ------------------------------------------------------------------

    async def update_entry(self, employee_id: int, entry_id: int, data: dict) -> dict:
        entry = await self.repo.get_by_id(entry_id)
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

        if entry.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas propriétaire de cette saisie",
            )

        if entry.status not in ("draft", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seules les saisies en brouillon ou rejetées peuvent être modifiées",
            )

        allowed = {"hours_worked", "description", "task_type", "billable_flag", "billing_rate", "notes"}
        updates = {k: v for k, v in data.items() if k in allowed and v is not None}

        if "hours_worked" in updates:
            hours = Decimal(str(updates["hours_worked"]))
            if hours < Decimal("0.25") or hours > Decimal("16"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Le nombre d'heures doit être entre 0.25 et 16",
                )
            updates["hours_worked"] = hours

        # If entry was rejected and is being edited, revert to draft
        if entry.status == "rejected":
            updates["status"] = "draft"
            updates["notes"] = None  # Clear rejection reason
            updates["approved_at"] = None

        updated = await self.repo.update(entry_id, **updates)
        await self.db.commit()
        await self.db.refresh(updated)
        return _entry_to_dict(updated)

    # ------------------------------------------------------------------
    # 2.13 — delete_entry
    # ------------------------------------------------------------------

    async def delete_entry(self, employee_id: int, entry_id: int) -> None:
        entry = await self.repo.get_by_id(entry_id)
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

        if entry.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas propriétaire de cette saisie",
            )

        if entry.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seules les saisies en brouillon peuvent être supprimées",
            )

        await self.repo.soft_delete(entry_id)
        await self.db.commit()

    async def get_draft_entries(self, employee_id: int) -> list[dict]:
        """Return all draft AND rejected entries for an employee (available for resubmission)."""
        from sqlalchemy import select as _sel
        from app.models.project import Project
        result = await self.db.execute(
            _sel(TimesheetEntry)
            .where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.status.in_(["draft", "rejected"]),
                TimesheetEntry.deleted_at.is_(None),
            )
            .order_by(TimesheetEntry.work_date.desc())
        )
        entries = result.scalars().all()
        # Enrich with project name (bulk query to avoid N+1)
        project_ids = list({e.project_id for e in entries})
        projects = {}
        if project_ids:
            proj_result = await self.db.execute(
                _sel(Project).where(Project.project_id.in_(project_ids))
            )
            projects = {p.project_id: p.project_name for p in proj_result.scalars().all()}
        result_list = []
        for e in entries:
            d = _entry_to_dict(e)
            d["project_name"] = projects.get(e.project_id, "—")
            result_list.append(d)
        return result_list

    async def get_all_entries(self, employee_id: int, skip: int = 0, limit: int = 100) -> list[dict]:
        """Return ALL entries for an employee (draft, submitted, approved, rejected)."""
        from sqlalchemy import select as _sel
        from app.models.project import Project
        result = await self.db.execute(
            _sel(TimesheetEntry)
            .where(
                TimesheetEntry.employee_id == employee_id,
                TimesheetEntry.deleted_at.is_(None),
            )
            .order_by(TimesheetEntry.work_date.desc())
            .offset(skip)
            .limit(limit)
        )
        entries = result.scalars().all()
        
        # Enrich with project name (bulk query to avoid N+1)
        project_ids = list({e.project_id for e in entries})
        projects = {}
        if project_ids:
            proj_result = await self.db.execute(
                _sel(Project).where(Project.project_id.in_(project_ids))
            )
            projects = {p.project_id: p.project_name for p in proj_result.scalars().all()}
        result_list = []
        for e in entries:
            d = _entry_to_dict(e)
            d["project_name"] = projects.get(e.project_id, "—")
            result_list.append(d)
        
        return result_list

    # ------------------------------------------------------------------
    # 2.14 — submit_week
    # ------------------------------------------------------------------

    async def submit_week(self, employee_id: int, week_str: str) -> dict:
        try:
            start_date, end_date = parse_iso_week(week_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid week format. Use YYYY-Www (e.g. 2025-W12)",
            )

        draft_entries = await self.repo.get_week_draft_entries(employee_id, start_date, end_date)

        if not draft_entries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No draft entries for this week",
            )

        existing_approval = await self.repo.get_approval_for_week(employee_id, start_date)
        
        # Case 1: Approval exists and is rejected/cancelled → resubmit entire week
        if existing_approval and existing_approval.status in ("rejected", "cancelled"):
            await self.repo.update_status(existing_approval.approval_id, status="pending")
            await self.repo.submit_week_entries(employee_id, start_date, end_date)
            await self.db.commit()
            
            logger.info(
                "Timesheet resubmitted: employee=%s week=%s approval=%s",
                employee_id, week_str, existing_approval.approval_id,
            )
            
            return {
                "week": week_str,
                "approval_id": existing_approval.approval_id,
                "status": "submitted",
                "entries_submitted": len(draft_entries),
            }

        # Case 2: Approval exists (pending/approved) → submit only new draft entries
        # This handles the case where some entries were rejected, corrected to draft, and need resubmission
        if existing_approval:
            await self.repo.submit_week_entries(employee_id, start_date, end_date)
            
            # If approval was approved but now has new submitted entries, revert to pending
            if existing_approval.status == "approved":
                await self.repo.update_status(existing_approval.approval_id, status="pending")
                existing_approval.status = "pending"
            
            await self.db.commit()
            
            logger.info(
                "Additional entries submitted: employee=%s week=%s approval=%s count=%s",
                employee_id, week_str, existing_approval.approval_id, len(draft_entries),
            )
            
            return {
                "week": week_str,
                "approval_id": existing_approval.approval_id,
                "status": existing_approval.status,
                "entries_submitted": len(draft_entries),
            }

        # Case 3: No approval exists → create new approval
        employee = await self.emp_repo.get_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        # Resolve manager_id via organization (Requirement 2.1)
        manager_id = employee.manager_id  # fallback
        if employee.org_id:
            try:
                from app.repositories.organization_repository import OrganizationRepository
                org_repo = OrganizationRepository(self.db)
                org = await org_repo.get_by_id(employee.org_id)
                if org and org.manager_id:
                    manager_id = org.manager_id
                elif not org:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={"detail": "Employee has no valid organization", "code": "no_valid_organization"},
                    )
            except HTTPException:
                raise
            except Exception:
                logger.warning("OrgSettings load failed", exc_info=True)

        approval = await self.repo.create_approval(employee_id, manager_id, start_date)
        await self.repo.submit_week_entries(employee_id, start_date, end_date)
        await self.db.commit()

        logger.info(
            "Timesheet submitted: employee=%s week=%s manager=%s approval=%s",
            employee_id, week_str, manager_id, approval.approval_id,
        )

        # Notification to manager (10.6)
        if manager_id:
            try:
                from app.tasks.notification_tasks import run_create_in_app_notification
                await run_create_in_app_notification(
                    employee_id=manager_id,
                    type="approval_submitted",
                    title="Timesheet submitted for approval",
                    message=f"A timesheet for week {start_date} has been submitted for your approval.",
                    entity_type="approval",
                    entity_id=approval.approval_id,
                    db=self.db,
                )
                await self.db.commit()
            except Exception:
                logger.warning("Timesheet notification to manager failed", exc_info=True)

        return {
            "week": week_str,
            "approval_id": approval.approval_id,
            "status": "submitted",
            "entries_submitted": len(draft_entries),
        }


def _entry_to_dict(entry) -> dict:
    return {
        "timesheet_entry_id": entry.timesheet_entry_id,
        "employee_id": entry.employee_id,
        "project_id": entry.project_id,
        "work_date": str(entry.work_date),
        "hours_worked": float(entry.hours_worked),
        "description": entry.description,
        "task_type": entry.task_type,
        "entry_type": getattr(entry, "entry_type", "normal"),
        "billable_flag": entry.billable_flag,
        "billing_rate": float(entry.billing_rate) if entry.billing_rate else None,
        "status": entry.status,
        "notes": entry.notes,
        "submitted_at": entry.submitted_at.isoformat() if entry.submitted_at else None,
        "approved_at": entry.approved_at.isoformat() if entry.approved_at else None,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }
