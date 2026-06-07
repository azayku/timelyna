"""OrganizationService — business logic for organizations."""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository

_VALID_MANAGER_ROLES = {"manager", "admin"}


class OrganizationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = OrganizationRepository(db)
        self.emp_repo = EmployeeRepository(db)

    async def _validate_manager(self, manager_id: int) -> None:
        """Raise 422 with code 'invalid_manager' if manager_id is not a valid manager/admin."""
        employee = await self.emp_repo.get_by_id(manager_id)
        if not employee or employee.role not in _VALID_MANAGER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"detail": "Invalid manager: employee not found or does not have manager/admin role", "code": "invalid_manager"},
            )

    async def create_organization(self, org_name: str, manager_id: int) -> Organization:
        """Create a new organization after validating the manager."""
        await self._validate_manager(manager_id)
        org = await self.repo.create(org_name=org_name, manager_id=manager_id)
        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def update_organization(self, org_id: int, **kwargs) -> Organization:
        """Update an organization, validating manager_id if provided."""
        if "manager_id" in kwargs and kwargs["manager_id"] is not None:
            await self._validate_manager(kwargs["manager_id"])
        org = await self.repo.update(org_id, **kwargs)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        await self.db.commit()
        return org

    async def soft_delete(self, org_id: int) -> None:
        """Soft-delete an organization."""
        org = await self.repo.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        await self.repo.soft_delete(org_id)
        await self.db.commit()

    async def list_organizations(self) -> list[dict]:
        """Return all active organizations enriched with employee_count."""
        orgs = await self.repo.list_active()
        result = []
        for org in orgs:
            count = await self.repo.get_employee_count(org.org_id)
            result.append({
                "org_id": org.org_id,
                "org_name": org.org_name,
                "manager_id": org.manager_id,
                "employee_count": count,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "updated_at": org.updated_at.isoformat() if org.updated_at else None,
            })
        return result
