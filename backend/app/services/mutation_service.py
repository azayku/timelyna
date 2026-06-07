"""MutationService — business logic for employee mutations between organizations."""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_mutation_log import EmployeeMutationLog
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.mutation_log_repository import MutationLogRepository
from app.repositories.organization_repository import OrganizationRepository


class MutationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.emp_repo = EmployeeRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.log_repo = MutationLogRepository(db)

    async def mutate_employee(
        self,
        employee_id: int,
        target_org_id: int,
        mutated_by: int,
        reason: Optional[str] = None,
    ) -> EmployeeMutationLog:
        """Transfer an employee to a different organization.

        Steps:
        1. Verify target_org_id is active.
        2. Verify employee is not manager of any organization.
        3. Capture from_org_id from employee.org_id.
        4. Update employees.org_id = target_org_id.
        5. Sync employees.manager_id = organizations.manager_id of target org.
        6. Insert mutation log.
        7. Trigger Celery task send_mutation_notification.
        8. Commit and return log.
        """
        # 1. Verify target org is active
        target_org = await self.org_repo.get_by_id(target_org_id)
        if not target_org:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"detail": "Target organization not found or inactive", "code": "invalid_target_organization"},
            )

        # 2. Verify employee is not manager of any organization
        managed_orgs = await self.org_repo.list_by_manager(employee_id)
        if managed_orgs:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"detail": "Employee is manager of an organization; reassign the organization manager first", "code": "employee_is_org_manager"},
            )

        # 3. Get employee and capture from_org_id
        employee = await self.emp_repo.get_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )
        from_org_id = employee.org_id

        # 4 & 5. Update org_id and sync manager_id
        await self.emp_repo.update(
            employee_id,
            org_id=target_org_id,
            manager_id=target_org.manager_id,
        )

        # 6. Insert mutation log
        log = await self.log_repo.create(
            employee_id=employee_id,
            from_org_id=from_org_id,
            to_org_id=target_org_id,
            mutated_by=mutated_by,
            reason=reason,
        )

        # 7. Trigger Celery notification (fire-and-forget; task defined in task 5.1)
        try:
            from app.tasks.email_tasks import task_send_mutation_notification
            task_send_mutation_notification.delay(
                employee_id=employee_id,
                target_org_id=target_org_id,
                mutated_by=mutated_by,
            )
        except Exception:  # noqa: BLE001
            pass

        # 8. Commit and return
        await self.db.commit()
        await self.db.refresh(log)
        return log
