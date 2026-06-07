"""MutationLogRepository — DB access for employee mutation logs."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_mutation_log import EmployeeMutationLog


class MutationLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        employee_id: int,
        from_org_id: int,
        to_org_id: int,
        mutated_by: int,
        reason: Optional[str] = None,
    ) -> EmployeeMutationLog:
        log = EmployeeMutationLog(
            employee_id=employee_id,
            from_org_id=from_org_id,
            to_org_id=to_org_id,
            mutated_by=mutated_by,
            reason=reason,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def list_by_employee(self, employee_id: int) -> list[EmployeeMutationLog]:
        result = await self.db.execute(
            select(EmployeeMutationLog)
            .where(EmployeeMutationLog.employee_id == employee_id)
            .order_by(EmployeeMutationLog.mutated_at.desc())
        )
        return list(result.scalars().all())
