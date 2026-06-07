"""Admin user management routes — /api/v1/admin/..."""
from __future__ import annotations

from datetime import datetime
from typing import Optional as _Opt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel as _BM2
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.repositories.auth_repository import AuthRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.auth import CreateUserRequest, UpdateUserRequest, UserResponse
from app.schemas.timesheet import (
    ClientResponse,
    CreateClientRequest,
    CreateProjectRequest,
    ProjectResponse,
    UpdateClientRequest,
    UpdateProjectRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_only = require_role("admin")


# ---------------------------------------------------------------------------
# Task 1.32 — POST /admin/users  (12d.25: now calls create_employee_or_pending)
# ---------------------------------------------------------------------------

class CreateUserResponse(_BM2):
    # Shared fields for both employee and pending responses
    type: _Opt[str] = "employee"
    # Employee fields
    employee_id: _Opt[int] = None
    email: _Opt[str] = None
    first_name: _Opt[str] = None
    last_name: _Opt[str] = None
    role: _Opt[str] = None
    employment_status: _Opt[str] = None
    manager_id: _Opt[int] = None
    org_id: _Opt[int] = None
    username: _Opt[str] = None
    must_change_password: bool = False
    address: _Opt[str] = None
    birth_date: _Opt[str] = None
    deactivation_scheduled_at: _Opt[str] = None
    preferred_language: str = 'fr'
    generated_username: _Opt[str] = None
    generated_password: _Opt[str] = None
    # Pending-specific fields
    id: _Opt[int] = None
    hire_date: _Opt[str] = None
    account_creation_date: _Opt[str] = None

    model_config = {"from_attributes": True}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AuthService(db)
    result = await svc.create_employee_or_pending(
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        role=body.role,
        manager_id=body.manager_id,
        birth_date=body.birth_date,
        address=body.address,
        hire_date=body.hire_date,
    )
    return result


# ---------------------------------------------------------------------------
# Task 1.33 — GET /admin/users
# ---------------------------------------------------------------------------

@router.get("/users", status_code=status.HTTP_200_OK)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=2000),
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = AuthRepository(db)
    offset = (page - 1) * page_size
    employees, total = await repo.list_employees(offset=offset, limit=page_size)
    return {
        "items": [UserResponse.model_validate(e) for e in employees],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ---------------------------------------------------------------------------
# Task 1.34 — PUT /admin/users/{id}
# ---------------------------------------------------------------------------

@router.put("/users/{employee_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    employee_id: int,
    body: UpdateUserRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    from fastapi import HTTPException
    repo = AuthRepository(db)
    employee = await repo.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = body.model_dump(exclude_none=True)
    if updates:
        await repo.update_employee(employee_id, **updates)
        await db.commit()
        await db.refresh(employee)

    return UserResponse.model_validate(employee)


# ---------------------------------------------------------------------------
# US-08 — PUT /admin/users/{id}/deactivate  &  /activate
# ---------------------------------------------------------------------------

@router.put("/users/{employee_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    employee_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Resp
    repo = AuthRepository(db)
    employee = await repo.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    svc = AuthService(db)
    await svc.deactivate_employee(employee_id)
    return _Resp(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/users/{employee_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_user(
    employee_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Resp
    repo = AuthRepository(db)
    employee = await repo.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    svc = AuthService(db)
    await svc.activate_employee(employee_id)
    return _Resp(status_code=status.HTTP_204_NO_CONTENT)


class ScheduleDeactivationRequest(_BM2):
    scheduled_at: datetime


@router.put("/users/{employee_id}/schedule-deactivation", status_code=status.HTTP_204_NO_CONTENT)
async def schedule_deactivation(
    employee_id: int,
    body: ScheduleDeactivationRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Resp
    repo = AuthRepository(db)
    employee = await repo.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    svc = AuthService(db)
    await svc.schedule_deactivation(employee_id, body.scheduled_at)
    return _Resp(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/users/{employee_id}/schedule-deactivation", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_scheduled_deactivation(
    employee_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Resp
    repo = AuthRepository(db)
    employee = await repo.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    svc = AuthService(db)
    await svc.cancel_scheduled_deactivation(employee_id)
    return _Resp(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Clients — GET/POST /admin/clients
# ===========================================================================

@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=2000),
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[ClientResponse]:
    repo = ClientRepository(db)
    clients = await repo.list_active(skip=skip, limit=limit)
    return [ClientResponse.model_validate(c) for c in clients]


@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: CreateClientRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    repo = ClientRepository(db)
    client = await repo.create(**body.model_dump())
    await db.commit()
    await db.refresh(client)
    return ClientResponse.model_validate(client)


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    repo = ClientRepository(db)
    client = await repo.get_by_id(client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    body: UpdateClientRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    repo = ClientRepository(db)
    client = await repo.get_by_id(client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    updates = body.model_dump(exclude_none=True)
    if updates:
        client = await repo.update(client_id, **updates)
        await db.commit()
        await db.refresh(client)
    return ClientResponse.model_validate(client)


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_client(
    client_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Response
    client_repo = ClientRepository(db)
    client = await client_repo.get_by_id(client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    proj_repo = ProjectRepository(db)
    await proj_repo.deactivate_by_client(client_id)
    await client_repo.deactivate(client_id)
    await db.commit()
    return _Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Projects — GET/POST /admin/projects
# ===========================================================================

@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects_admin(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=2000),
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    repo = ProjectRepository(db)
    projects = await repo.list_all_active(skip=skip, limit=limit)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: CreateProjectRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    from app.utils.project_code import ensure_unique_project_code
    repo = ProjectRepository(db)
    data = body.model_dump()
    if not data.get("project_code"):
        data["project_code"] = await ensure_unique_project_code(db)
    project = await repo.create(**data)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    body: UpdateProjectRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    updates = body.model_dump(exclude_none=True)
    if updates:
        project = await repo.update(project_id, **updates)
        await db.commit()
        await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_project(
    project_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Response
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await repo.deactivate(project_id)
    await db.commit()
    return _Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Skill Rates — GET/POST/PUT/DELETE /admin/skill-rates
# ===========================================================================

from decimal import Decimal as _Decimal
from pydantic import BaseModel as _SkillModel


class CreateSkillRateRequest(_SkillModel):
    skill_name: str
    billing_rate: _Decimal
    description: _Opt[str] = None


class UpdateSkillRateRequest(_SkillModel):
    skill_name: _Opt[str] = None
    billing_rate: _Opt[_Decimal] = None
    description: _Opt[str] = None


class SkillRateResponse(_SkillModel):
    id: int
    org_id: int
    skill_name: str
    billing_rate: _Decimal
    description: _Opt[str]
    created_at: _Opt[datetime] = None

    model_config = {"from_attributes": True}


@router.get("/skill-rates", response_model=list[SkillRateResponse])
async def list_skill_rates(
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[SkillRateResponse]:
    from app.repositories.skill_rate_repository import SkillRateRepository
    repo = SkillRateRepository(db)
    org_id = current_user.get("org_id", 1)
    rates = await repo.list_by_org(org_id=org_id)
    return [SkillRateResponse.model_validate(r) for r in rates]


@router.post("/skill-rates", response_model=SkillRateResponse, status_code=status.HTTP_201_CREATED)
async def create_skill_rate(
    body: CreateSkillRateRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> SkillRateResponse:
    from app.repositories.skill_rate_repository import SkillRateRepository
    repo = SkillRateRepository(db)
    rate = await repo.create(
        skill_name=body.skill_name,
        billing_rate=body.billing_rate,
        description=body.description,
    )
    await db.commit()
    await db.refresh(rate)
    return SkillRateResponse.model_validate(rate)


@router.put("/skill-rates/{rate_id}", response_model=SkillRateResponse)
async def update_skill_rate(
    rate_id: int,
    body: UpdateSkillRateRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> SkillRateResponse:
    from app.repositories.skill_rate_repository import SkillRateRepository
    repo = SkillRateRepository(db)
    updates = body.model_dump(exclude_none=True)
    rate = await repo.update(rate_id, **updates)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill rate not found")
    await db.commit()
    await db.refresh(rate)
    return SkillRateResponse.model_validate(rate)


@router.delete("/skill-rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill_rate(
    rate_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response as _Response
    from app.repositories.skill_rate_repository import SkillRateRepository
    repo = SkillRateRepository(db)
    rate = await repo.get_by_id(rate_id)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill rate not found")
    await repo.delete(rate_id)
    await db.commit()
    return _Response(status_code=status.HTTP_204_NO_CONTENT)

from datetime import datetime, timezone
from pydantic import BaseModel as _BaseModel

# ===========================================================================
# Employee availability — GET /admin/availability
# ===========================================================================

_admin_or_manager = require_role("admin", "manager")


@router.get("/availability")
async def get_availability(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    department: str | None = Query(default=None),
    project_id: int | None = Query(default=None),
    _: dict = Depends(_admin_or_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get employee availability for a date range."""
    from datetime import date as _date
    from app.services.availability_service import AvailabilityService

    try:
        sd = _date.fromisoformat(start_date)
        ed = _date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Validate max 31 days
    delta = (ed - sd).days
    if delta < 0 or delta > 31:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Date range must be between 1 and 31 days",
        )

    svc = AvailabilityService(db)
    return await svc.get_availability(sd, ed, department, project_id)


# ===========================================================================
# Team availability — GET /admin/projects/{id}/team-availability
# ===========================================================================


@router.get("/projects/{project_id}/team-availability")
async def get_team_availability(
    project_id: int,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    _: dict = Depends(_admin_or_manager),
    db: AsyncSession = Depends(get_db),
) -> list:
    from datetime import date as _date
    from app.services.project_availability_service import ProjectAvailabilityService

    try:
        sd = _date.fromisoformat(start_date)
        ed = _date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    svc = ProjectAvailabilityService(db)
    return await svc.get_team_availability(sd, ed)


from app.services.license_service import LicenseService
from app.models.organization_license import OrganizationLicense
from sqlalchemy import select as _select


class ActivateLicenseRequest(_BaseModel):
    license_token: str


# ===========================================================================
# Email Templates — GET/PUT /admin/email-templates
# ===========================================================================

class EmailTemplateResponse(_BaseModel):
    key: str
    subject: str
    html_body: str
    text_body: _Opt[str]
    is_custom: bool
    updated_at: _Opt[str]


class UpdateEmailTemplateRequest(_BaseModel):
    subject: str
    html_body: str


class SendPreviewRequest(_BaseModel):
    to_email: str


@router.get("/email-templates", response_model=list[EmailTemplateResponse])
async def list_email_templates(
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[EmailTemplateResponse]:
    """List all available email templates."""
    from app.services.email_template_service import EmailTemplateService
    svc = EmailTemplateService(db)
    templates = await svc.list_templates()
    return [EmailTemplateResponse.model_validate(t) for t in templates]


@router.get("/email-templates/{key}", response_model=EmailTemplateResponse)
async def get_email_template(
    key: str,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> EmailTemplateResponse:
    """Get a specific email template by key."""
    from app.services.email_template_service import EmailTemplateService
    svc = EmailTemplateService(db)
    try:
        template = await svc.get_template(key)
        return EmailTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/email-templates/{key}", response_model=EmailTemplateResponse)
async def update_email_template(
    key: str,
    body: UpdateEmailTemplateRequest,
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> EmailTemplateResponse:
    """Update an email template (creates custom version in DB)."""
    from app.services.email_template_service import EmailTemplateService
    svc = EmailTemplateService(db)
    try:
        updated_by = current_user.get("employee_id")
        template = await svc.update_template(
            key=key,
            subject=body.subject,
            html_body=body.html_body,
            updated_by=updated_by,
        )
        return EmailTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/email-templates/{key}/preview", status_code=status.HTTP_204_NO_CONTENT)
async def send_email_template_preview(
    key: str,
    body: SendPreviewRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Send a preview email with sample data."""
    from fastapi import Response as _Resp
    from app.services.email_template_service import EmailTemplateService
    from app.utils.email import send_email
    
    svc = EmailTemplateService(db)
    try:
        # Get template
        template = await svc.get_template(key)
        
        # Sample context data
        sample_context = {
            "first_name": "Jean",
            "last_name": "Martin",
            "username": "martjean",
            "setup_link": "https://example.com/setup?token=sample123",
            "reset_link": "https://example.com/reset?token=sample456",
            "org_name": "Mon Organisation",
        }
        
        # Render template
        subject, html_body = await svc.render_template(key, sample_context)
        
        # Send preview email (send_email is synchronous)
        send_email(
            to=body.to_email,
            subject=f"[PREVIEW] {subject}",
            body=html_body,
        )
        
        return _Resp(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send preview: {str(e)}",
        )


@router.delete("/email-templates/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def reset_email_template(
    key: str,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Reset an email template to default (delete custom version)."""
    from fastapi import Response as _Resp
    from app.services.email_template_service import EmailTemplateService
    
    svc = EmailTemplateService(db)
    try:
        await svc.reset_to_default(key)
        return _Resp(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/license/activate", status_code=status.HTTP_200_OK)
async def activate_license(
    body: ActivateLicenseRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Validate license JWT locally and store in organization_licenses."""
    svc = LicenseService()
    payload = svc.validate_local(body.license_token)

    org_id = payload.get("organizationId", "default")
    pack = payload.get("pack")
    exp = payload.get("exp")
    grace = payload.get("grace")
    features = payload.get("features", {})
    limits = payload.get("limits", {})

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
    grace_ends_at = datetime.fromtimestamp(grace, tz=timezone.utc) if grace else None
    now = datetime.now(timezone.utc)

    # Upsert: update if exists, insert if not
    result = await db.execute(_select(OrganizationLicense).where(OrganizationLicense.org_id == org_id))
    existing = result.scalar_one_or_none()

    if existing:
        existing.license_token = body.license_token
        existing.pack = pack
        existing.activated_at = now
        existing.expires_at = expires_at
        existing.grace_ends_at = grace_ends_at
        existing.last_validated_at = now
        existing.validation_status = "valid"
    else:
        lic = OrganizationLicense(
            org_id=org_id,
            license_token=body.license_token,
            pack=pack,
            activated_at=now,
            expires_at=expires_at,
            grace_ends_at=grace_ends_at,
            last_validated_at=now,
            validation_status="valid",
        )
        db.add(lic)

    await db.commit()

    return {
        "pack": pack,
        "features": features,
        "limits": limits,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }


@router.get("/license/status", status_code=status.HTTP_200_OK)
async def license_status(
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return current license status for the organization."""
    result = await db.execute(_select(OrganizationLicense).limit(1))
    lic = result.scalar_one_or_none()

    if not lic:
        return {"status": "no_license"}

    svc = LicenseService()
    try:
        payload = svc.validate_local(lic.license_token)
    except Exception:
        return {
            "status": "invalid",
            "validation_status": lic.validation_status,
        }

    exp = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
    days_until_expiry: int | None = None
    if expires_at:
        delta = expires_at - datetime.now(timezone.utc)
        days_until_expiry = max(0, delta.days)

    return {
        "pack": payload.get("pack"),
        "features": payload.get("features", {}),
        "limits": payload.get("limits", {}),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "days_until_expiry": days_until_expiry,
        "validation_status": lic.validation_status,
    }


# ===========================================================================
# Team assignment — PUT /admin/projects/{id}/team
# ===========================================================================

from pydantic import BaseModel as _BM
from typing import List as _List


class AssignTeamRequest(_BM):
    employee_ids: _List[int]


@router.put("/projects/{project_id}/team", response_model=ProjectResponse)
async def assign_team(
    project_id: int,
    body: AssignTeamRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Assign (replace) the team members list for a project."""
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project = await repo.update(project_id, team_members=body.employee_ids)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


# ===========================================================================
# Employees list (for team picker)
# ===========================================================================

@router.get("/employees", status_code=status.HTTP_200_OK)
async def list_all_employees(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all active employees — used by admin team picker."""
    repo = AuthRepository(db)
    employees, total = await repo.list_employees(offset=skip, limit=limit)
    return {
        "items": [UserResponse.model_validate(e) for e in employees],
        "total": total,
    }


# ===========================================================================
# Org Settings — GET/PUT /admin/settings
# ===========================================================================

from pydantic import BaseModel as _SettingsModel
from decimal import Decimal as _Dec
from app.models.org_settings import OrgSettings
from sqlalchemy import select as _sel


class OrgSettingsRequest(_SettingsModel):
    org_name: str | None = None
    standard_hours_per_day: _Dec | None = None
    max_hours_per_day: _Dec | None = None
    overtime_rate_multiplier: _Dec | None = None
    travel_rate_multiplier: _Dec | None = None
    default_currency: str | None = None
    account_creation_lead_days: int | None = None
    next_week_display_day: int | None = None


@router.get("/settings")
async def get_org_settings(
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    org_id = current_user.get("org_id", 1)
    result = await db.execute(_sel(OrgSettings).where(OrgSettings.org_id == org_id))
    s = result.scalar_one_or_none()
    if not s:
        # Return defaults
        return {
            "org_name": "Mon Organisation",
            "standard_hours_per_day": 8.0,
            "max_hours_per_day": 24.0,
            "overtime_rate_multiplier": 1.25,
            "travel_rate_multiplier": 0.50,
            "default_currency": "EUR",
            "account_creation_lead_days": 2,
            "next_week_display_day": 2,
        }
    return {
        "org_name": s.org_name,
        "standard_hours_per_day": float(s.standard_hours_per_day),
        "max_hours_per_day": float(s.max_hours_per_day),
        "overtime_rate_multiplier": float(s.overtime_rate_multiplier),
        "travel_rate_multiplier": float(s.travel_rate_multiplier),
        "default_currency": s.default_currency,
        "account_creation_lead_days": s.account_creation_lead_days,
        "next_week_display_day": s.next_week_display_day,
    }


@router.put("/settings")
async def update_org_settings(
    body: OrgSettingsRequest,
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    org_id = current_user.get("org_id", 1)
    result = await db.execute(_sel(OrgSettings).where(OrgSettings.org_id == org_id))
    s = result.scalar_one_or_none()
    if not s:
        s = OrgSettings(org_id=org_id)
        db.add(s)
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return {
        "org_name": s.org_name,
        "standard_hours_per_day": float(s.standard_hours_per_day),
        "max_hours_per_day": float(s.max_hours_per_day),
        "overtime_rate_multiplier": float(s.overtime_rate_multiplier),
        "travel_rate_multiplier": float(s.travel_rate_multiplier),
        "default_currency": s.default_currency,
        "account_creation_lead_days": s.account_creation_lead_days,
        "next_week_display_day": s.next_week_display_day,
    }


# ===========================================================================
# Finance Pro License — POST/GET /admin/finance-license/activate|status
# ===========================================================================

from app.utils.module_license import validate_key as _validate_module_key
from app.models.module_license import ModuleLicense


class ActivateFinanceLicenseRequest(_BM):
    license_key: str


class FinanceLicenseStatusResponse(_BM):
    active: bool
    expiry_date: str | None = None
    days_remaining: int | None = None
    error: str | None = None


@router.post("/finance-license/activate", status_code=status.HTTP_200_OK)
async def activate_finance_license(
    body: ActivateFinanceLicenseRequest,
    current_user: dict = Depends(require_role("admin", "finance")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Validate and activate Finance Pro license key."""
    # Validate the license key
    validation_result = _validate_module_key(body.license_key)
    
    if not validation_result["valid"]:
        error_msg = validation_result.get("error", "Invalid license key")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    expiry_date = validation_result["expiry_date"]
    
    org_id = current_user.get("org_id", 1)
    
    # Store in module_licenses table
    result = await db.execute(
        _sel(ModuleLicense).where(
            ModuleLicense.org_id == org_id,
            ModuleLicense.module_name == "finance_pro"
        )
    )
    module_license = result.scalar_one_or_none()
    
    if not module_license:
        module_license = ModuleLicense(
            org_id=org_id,
            module_name="finance_pro",
            license_key=body.license_key,
            expires_at=expiry_date
        )
        db.add(module_license)
    else:
        module_license.license_key = body.license_key
        module_license.expires_at = expiry_date
    
    await db.commit()
    await db.refresh(module_license)
    
    # Calculate days remaining
    from datetime import date as _date
    today = _date.today()
    days_remaining = (expiry_date - today).days if expiry_date else None
    
    return {
        "success": True,
        "expiry_date": expiry_date.isoformat() if expiry_date else None,
        "days_remaining": days_remaining,
    }


@router.get("/finance-license/status", response_model=FinanceLicenseStatusResponse)
async def get_finance_license_status(
    current_user: dict = Depends(require_role("admin", "finance")),
    db: AsyncSession = Depends(get_db),
) -> FinanceLicenseStatusResponse:
    """Get current Finance Pro license status."""
    from datetime import date as _date
    
    org_id = current_user.get("org_id", 1)
    
    # Query module_licenses table
    result = await db.execute(
        _sel(ModuleLicense).where(
            ModuleLicense.org_id == org_id,
            ModuleLicense.module_name == "finance_pro"
        )
    )
    module_license = result.scalar_one_or_none()
    
    if not module_license:
        return FinanceLicenseStatusResponse(
            active=False,
            expiry_date=None,
            days_remaining=None,
            error="No license key activated"
        )
    
    # Validate the stored license key
    validation_result = _validate_module_key(module_license.license_key)
    
    if not validation_result["valid"]:
        error_msg = validation_result.get("error", "Invalid license")
        return FinanceLicenseStatusResponse(
            active=False,
            expiry_date=module_license.expires_at.isoformat() if module_license.expires_at else None,
            days_remaining=None,
            error=error_msg
        )
    
    # Calculate days remaining
    expiry_date = validation_result["expiry_date"]
    today = _date.today()
    days_remaining = (expiry_date - today).days if expiry_date else None
    
    return FinanceLicenseStatusResponse(
        active=True,
        expiry_date=expiry_date.isoformat() if expiry_date else None,
        days_remaining=days_remaining,
        error=None
    )


# ===========================================================================
# Module trial — POST /admin/module-licenses/{module}/trial
# Generates a 15-day trial key and activates it immediately.
# One trial per module per org — returns 409 if already used.
# ===========================================================================

from app.utils.module_license import generate_key as _generate_module_key

_TRIAL_DAYS = 15
_ALLOWED_TRIAL_MODULES = {"finance_pro", "advanced_analytics", "api_access", "multi_org"}


@router.post("/module-licenses/{module_name}/trial", status_code=status.HTTP_200_OK)
async def start_module_trial(
    module_name: str,
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Activate a 15-day free trial for a module. One trial per org per module."""
    from datetime import date as _date, timedelta as _td, timezone as _tz, datetime as _dt

    if module_name not in _ALLOWED_TRIAL_MODULES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown module")

    org_id = current_user.get("org_id", 1)

    # Check if a license (trial or paid) already exists
    result = await db.execute(
        _sel(ModuleLicense).where(
            ModuleLicense.org_id == org_id,
            ModuleLicense.module_name == module_name,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A license or trial already exists for this module.",
        )

    # Generate a trial key expiring in 15 days
    expiry = _date.today() + _td(days=_TRIAL_DAYS)
    trial_key = _generate_module_key(expiry)

    # Persist
    module_license = ModuleLicense(
        org_id=org_id,
        module_name=module_name,
        license_key=trial_key,
        expires_at=expiry,
    )
    db.add(module_license)
    await db.commit()
    await db.refresh(module_license)

    expires_ts = int(_dt.combine(expiry, _dt.min.time()).replace(tzinfo=_tz.utc).timestamp())

    return {
        "module": module_name,
        "trial": True,
        "expires_at": expiry.isoformat(),
        "expires_ts": expires_ts,
        "days_remaining": _TRIAL_DAYS,
    }


@router.get("/module-licenses/status", status_code=status.HTTP_200_OK)
async def get_all_module_licenses_status(
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return status of all known modules for the org."""
    from datetime import date as _date

    org_id = current_user.get("org_id", 1)

    result = await db.execute(
        _sel(ModuleLicense).where(ModuleLicense.org_id == org_id)
    )
    licenses = result.scalars().all()

    modules: dict[str, dict] = {}
    for lic in licenses:
        validation = _validate_module_key(lic.license_key)
        days = (lic.expires_at - _date.today()).days if lic.expires_at else None
        modules[lic.module_name] = {
            "active": validation["valid"],
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
            "expires_ts": int(__import__('datetime').datetime.combine(
                lic.expires_at, __import__('datetime').datetime.min.time()
            ).replace(tzinfo=__import__('datetime').timezone.utc).timestamp()) if lic.expires_at else None,
            "days_remaining": max(0, days) if days is not None else None,
        }

    return {"modules": modules}


# ===========================================================================
# 12d.8 — Proxy Admin routes
# ===========================================================================

from app.core.module_license_deps import require_finance_license as _require_finance_license
from pydantic import BaseModel as _ProxyModel


class ProxyStartRequest(_ProxyModel):
    employee_id: int


class ProxyEndRequest(_ProxyModel):
    proxy_log_id: int
    entries_created: int = 0


_proxy_deps = [Depends(_admin_only), Depends(_require_finance_license)]


@router.post("/proxy/start", status_code=status.HTTP_200_OK)
async def proxy_start(
    body: ProxyStartRequest,
    current_user: dict = Depends(_admin_only),
    _lic=Depends(_require_finance_license),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start a proxy session: admin impersonates an employee."""
    svc = AuthService(db)
    return await svc.create_proxy_token(
        admin_id=current_user["employee_id"],
        employee_id=body.employee_id,
    )


@router.post("/proxy/end", status_code=status.HTTP_200_OK)
async def proxy_end(
    body: ProxyEndRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """End a proxy session: record ended_at and entries_created."""
    svc = AuthService(db)
    await svc.end_proxy_session(body.proxy_log_id, body.entries_created)
    return {"ok": True}


@router.get("/proxy/logs", status_code=status.HTTP_200_OK)
async def proxy_logs(
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List all proxy audit log sessions with admin/employee names and duration."""
    from sqlalchemy import select as _s
    from app.models.proxy_audit_log import ProxyAuditLog
    from app.models.employee import Employee as _Emp

    AdminEmp = _Emp.__table__.alias("admin_emp")
    TargetEmp = _Emp.__table__.alias("target_emp")

    result = await db.execute(_s(ProxyAuditLog).order_by(ProxyAuditLog.started_at.desc()))
    logs = result.scalars().all()

    # Enrich with names
    output = []
    for log in logs:
        admin_res = await db.execute(_s(_Emp).where(_Emp.employee_id == log.admin_id))
        admin = admin_res.scalar_one_or_none()
        emp_res = await db.execute(_s(_Emp).where(_Emp.employee_id == log.employee_id))
        emp = emp_res.scalar_one_or_none()

        duration_seconds = None
        if log.ended_at and log.started_at:
            duration_seconds = int((log.ended_at - log.started_at).total_seconds())

        output.append({
            "id": log.id,
            "admin_name": f"{admin.first_name} {admin.last_name}" if admin else str(log.admin_id),
            "employee_name": f"{emp.first_name} {emp.last_name}" if emp else str(log.employee_id),
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "ended_at": log.ended_at.isoformat() if log.ended_at else None,
            "duration_seconds": duration_seconds,
            "entries_created": log.entries_created,
        })
    return output


# ===========================================================================
# 12d.24 — Pending employees routes
# ===========================================================================

from datetime import date as _date_type
from pydantic import BaseModel as _PendingModel


class CreatePendingEmployeeRequest(_PendingModel):
    first_name: str
    last_name: str
    email: str
    role: str
    manager_id: _Opt[int] = None
    birth_date: _Opt[_date_type] = None
    address: _Opt[str] = None
    hire_date: _date_type
    account_creation_date: _Opt[_date_type] = None


@router.get("/pending-employees", status_code=status.HTTP_200_OK)
async def list_pending_employees(
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List all pending employees."""
    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    repo = PendingEmployeeRepository(db)
    items = await repo.list_all()
    return [
        {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "email": p.email,
            "role": p.role,
            "hire_date": str(p.hire_date) if p.hire_date else None,
            "account_creation_date": str(p.account_creation_date) if p.account_creation_date else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in items
    ]


@router.post("/pending-employees", status_code=status.HTTP_201_CREATED)
async def create_pending_employee(
    body: CreatePendingEmployeeRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Directly create a pending employee (bypass auto-logic)."""
    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    repo = PendingEmployeeRepository(db)
    p = await repo.create(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        role=body.role,
        manager_id=body.manager_id,
        birth_date=body.birth_date,
        address=body.address,
        hire_date=body.hire_date,
        account_creation_date=body.account_creation_date or body.hire_date,
    )
    await db.commit()
    await db.refresh(p)
    return {
        "id": p.id,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "email": p.email,
        "role": p.role,
        "hire_date": str(p.hire_date) if p.hire_date else None,
        "account_creation_date": str(p.account_creation_date) if p.account_creation_date else None,
    }


@router.delete("/pending-employees/{pending_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_pending_employee(
    pending_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Cancel (delete) a pending employee."""
    from fastapi import Response as _Resp
    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    repo = PendingEmployeeRepository(db)
    p = await repo.get_by_id(pending_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending employee not found")
    await repo.delete(pending_id)
    await db.commit()
    return _Resp(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/pending-employees/{pending_id}/activate", status_code=status.HTTP_201_CREATED)
async def force_activate_pending_employee(
    pending_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Force immediate activation of a pending employee."""
    from app.repositories.pending_employee_repository import PendingEmployeeRepository
    from app.services.auth_service import AuthService as _AuthSvc
    repo = PendingEmployeeRepository(db)
    p = await repo.get_by_id(pending_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending employee not found")
    svc = _AuthSvc(db)
    employee = await svc.create_employee(
        email=p.email,
        first_name=p.first_name,
        last_name=p.last_name,
        role=p.role,
        manager_id=p.manager_id,
        birth_date=p.birth_date,
        address=p.address,
    )
    await repo.delete(pending_id)
    await db.commit()
    return {
        "type": "employee",
        "id": employee.employee_id,
        "email": employee.email,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
    }


# ===========================================================================
# Spec 13 — Multi-org: Organizations CRUD  (6.1)
# ===========================================================================

from app.schemas.multi_org import (
    CreateOrganizationRequest as _CreateOrgReq,
    UpdateOrganizationRequest as _UpdateOrgReq,
    OrganizationResponse as _OrgResp,
    AddEmployeeSkillRequest as _AddSkillReq,
    EmployeeSkillResponse as _EmpSkillResp,
    MutateEmployeeRequest as _MutateReq,
    MutationLogResponse as _MutLogResp,
    ProjectSkillRequirement as _ProjSkillReq,
    SuggestedEmployeeResponse as _SuggestedEmpResp,
)
from app.services.organization_service import OrganizationService as _OrgSvc
from app.services.mutation_service import MutationService as _MutSvc
from app.services.employee_suggestion_service import EmployeeSuggestionService as _SuggestSvc
from app.repositories.employee_skill_repository import EmployeeSkillRepository as _EmpSkillRepo
from app.repositories.project_skill_repository import ProjectSkillRepository as _ProjSkillRepo
from app.repositories.mutation_log_repository import MutationLogRepository as _MutLogRepo
from app.repositories.skill_rate_repository import SkillRateRepository as _SkillRateRepo


@router.get("/organizations", response_model=list[_OrgResp])
async def list_organizations(
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[_OrgResp]:
    """List all active organizations with employee_count."""
    svc = _OrgSvc(db)
    orgs = await svc.list_organizations()
    return [_OrgResp(**o) for o in orgs]


@router.post("/organizations", response_model=_OrgResp, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: _CreateOrgReq,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> _OrgResp:
    """Create a new organization. Validates that manager_id has role manager/admin."""
    svc = _OrgSvc(db)
    org = await svc.create_organization(org_name=body.org_name, manager_id=body.manager_id)
    count = await svc.repo.get_employee_count(org.org_id)
    return _OrgResp(
        org_id=org.org_id,
        org_name=org.org_name,
        manager_id=org.manager_id,
        employee_count=count,
        created_at=org.created_at.isoformat() if org.created_at else None,
        updated_at=org.updated_at.isoformat() if org.updated_at else None,
    )


@router.get("/organizations/{org_id}", response_model=_OrgResp)
async def get_organization(
    org_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> _OrgResp:
    """Get a single organization by ID."""
    from app.repositories.organization_repository import OrganizationRepository as _OrgRepo
    repo = _OrgRepo(db)
    org = await repo.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    count = await repo.get_employee_count(org_id)
    return _OrgResp(
        org_id=org.org_id,
        org_name=org.org_name,
        manager_id=org.manager_id,
        employee_count=count,
        created_at=org.created_at.isoformat() if org.created_at else None,
        updated_at=org.updated_at.isoformat() if org.updated_at else None,
    )


@router.put("/organizations/{org_id}", response_model=_OrgResp)
async def update_organization(
    org_id: int,
    body: _UpdateOrgReq,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> _OrgResp:
    """Update an organization. Validates manager_id if provided."""
    svc = _OrgSvc(db)
    updates = body.model_dump(exclude_none=True)
    org = await svc.update_organization(org_id, **updates)
    count = await svc.repo.get_employee_count(org_id)
    return _OrgResp(
        org_id=org.org_id,
        org_name=org.org_name,
        manager_id=org.manager_id,
        employee_count=count,
        created_at=org.created_at.isoformat() if org.created_at else None,
        updated_at=org.updated_at.isoformat() if org.updated_at else None,
    )


@router.delete("/organizations/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an organization (sets deleted_at)."""
    from fastapi import Response as _Resp
    svc = _OrgSvc(db)
    await svc.soft_delete(org_id)
    return _Resp(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Spec 13 — Employee skills  (6.2)
# ===========================================================================

@router.get("/employees/{employee_id}/skills", response_model=list[_EmpSkillResp])
async def list_employee_skills(
    employee_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[_EmpSkillResp]:
    """List all skills assigned to an employee."""
    from app.repositories.auth_repository import AuthRepository as _AuthRepo
    emp_repo = _AuthRepo(db)
    employee = await emp_repo.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    skill_repo = _EmpSkillRepo(db)
    skills = await skill_repo.list_by_employee(employee_id)

    # Enrich with skill_name and billing_rate via SkillRate
    rate_repo = _SkillRateRepo(db)
    result = []
    for s in skills:
        rate = await rate_repo.get_by_id(s.skill_rate_id)
        result.append(_EmpSkillResp(
            id=s.id,
            employee_id=s.employee_id,
            skill_rate_id=s.skill_rate_id,
            skill_name=rate.skill_name if rate else str(s.skill_rate_id),
            billing_rate=rate.billing_rate if rate else None,
            assigned_at=s.assigned_at.isoformat() if s.assigned_at else None,
        ))
    return result


@router.post(
    "/employees/{employee_id}/skills",
    response_model=_EmpSkillResp,
    status_code=status.HTTP_201_CREATED,
)
async def add_employee_skill(
    employee_id: int,
    body: _AddSkillReq,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> _EmpSkillResp:
    """Add a skill to an employee. Returns 409 if already assigned, 422 if org mismatch."""
    from app.repositories.auth_repository import AuthRepository as _AuthRepo
    emp_repo = _AuthRepo(db)
    employee = await emp_repo.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Validate skill belongs to the same org as the employee
    rate_repo = _SkillRateRepo(db)
    rate = await rate_repo.get_by_id(body.skill_rate_id)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill rate not found")
    if rate.org_id != employee.org_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "Skill belongs to a different organization", "code": "skill_org_mismatch"},
        )

    skill_repo = _EmpSkillRepo(db)
    try:
        skill = await skill_repo.add(employee_id=employee_id, skill_rate_id=body.skill_rate_id)
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"detail": "Employee already has this skill", "code": "skill_already_assigned"},
            )
        raise
    await db.commit()
    await db.refresh(skill)
    return _EmpSkillResp(
        id=skill.id,
        employee_id=skill.employee_id,
        skill_rate_id=skill.skill_rate_id,
        skill_name=rate.skill_name,
        billing_rate=rate.billing_rate,
        assigned_at=skill.assigned_at.isoformat() if skill.assigned_at else None,
    )


@router.delete(
    "/employees/{employee_id}/skills/{skill_rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_employee_skill(
    employee_id: int,
    skill_rate_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill from an employee."""
    from fastapi import Response as _Resp
    skill_repo = _EmpSkillRepo(db)
    await skill_repo.remove(employee_id=employee_id, skill_rate_id=skill_rate_id)
    await db.commit()
    return _Resp(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Spec 13 — Employee mutation  (6.3)
# ===========================================================================

@router.post(
    "/employees/{employee_id}/mutate",
    response_model=_MutLogResp,
    status_code=status.HTTP_200_OK,
)
async def mutate_employee(
    employee_id: int,
    body: _MutateReq,
    current_user: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> _MutLogResp:
    """Transfer an employee to a different organization."""
    svc = _MutSvc(db)
    log = await svc.mutate_employee(
        employee_id=employee_id,
        target_org_id=body.target_org_id,
        mutated_by=current_user["employee_id"],
        reason=body.reason,
    )
    return _MutLogResp(
        id=log.id,
        employee_id=log.employee_id,
        from_org_id=log.from_org_id,
        to_org_id=log.to_org_id,
        mutated_by=log.mutated_by,
        mutated_at=log.mutated_at.isoformat() if log.mutated_at else None,
        reason=log.reason,
    )


@router.get(
    "/employees/{employee_id}/mutation-history",
    response_model=list[_MutLogResp],
)
async def get_mutation_history(
    employee_id: int,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[_MutLogResp]:
    """Return the full mutation history for an employee."""
    log_repo = _MutLogRepo(db)
    logs = await log_repo.list_by_employee(employee_id)
    return [
        _MutLogResp(
            id=log.id,
            employee_id=log.employee_id,
            from_org_id=log.from_org_id,
            to_org_id=log.to_org_id,
            mutated_by=log.mutated_by,
            mutated_at=log.mutated_at.isoformat() if log.mutated_at else None,
            reason=log.reason,
        )
        for log in logs
    ]


# ===========================================================================
# Spec 13 — Project suggested employees  (6.4)
# ===========================================================================

@router.get(
    "/projects/{project_id}/suggested-employees",
    response_model=list[_SuggestedEmpResp],
)
async def get_suggested_employees(
    project_id: int,
    _: dict = Depends(_admin_or_manager),
    db: AsyncSession = Depends(get_db),
) -> list[_SuggestedEmpResp]:
    """Return ranked list of available, skilled employees for a project."""
    svc = _SuggestSvc(db)
    suggestions = await svc.suggest_employees(project_id)
    return [_SuggestedEmpResp(**s) for s in suggestions]


# ===========================================================================
# Spec 13 — Extend project routes with required_skills  (6.5)
# ===========================================================================
# Override the existing create_project and update_project routes to also
# persist required_skills via ProjectSkillRepository.
# FastAPI uses the last registered route for a given path+method, so these
# new definitions shadow the earlier ones defined above.

from pydantic import BaseModel as _ProjExtModel
from typing import Optional as _OptType
from decimal import Decimal as _DecType
from datetime import date as _DateType


class CreateProjectWithSkillsRequest(_ProjExtModel):
    """Extended CreateProjectRequest that also accepts required_skills."""
    client_id: int
    project_name: str
    project_code: _OptType[str] = None
    description: _OptType[str] = None
    status: str = "active"
    start_date: _DateType
    end_date: _OptType[_DateType] = None
    budget_hours: _OptType[_DecType] = None
    budget_amount: _OptType[_DecType] = None
    billing_rate: _DecType
    manager_id: int
    team_members: _OptType[list[int]] = None
    required_skills: _OptType[list[_ProjSkillReq]] = None


class UpdateProjectWithSkillsRequest(_ProjExtModel):
    """Extended UpdateProjectRequest that also accepts required_skills."""
    project_name: _OptType[str] = None
    description: _OptType[str] = None
    status: _OptType[str] = None
    end_date: _OptType[_DateType] = None
    budget_hours: _OptType[_DecType] = None
    budget_amount: _OptType[_DecType] = None
    billing_rate: _OptType[_DecType] = None
    manager_id: _OptType[int] = None
    team_members: _OptType[list[int]] = None
    required_skills: _OptType[list[_ProjSkillReq]] = None


@router.post(
    "/projects/with-skills",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_with_skills(
    body: CreateProjectWithSkillsRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a project and optionally persist required_skills."""
    from app.utils.project_code import ensure_unique_project_code
    repo = ProjectRepository(db)
    data = body.model_dump(exclude={"required_skills"})
    if not data.get("project_code"):
        data["project_code"] = await ensure_unique_project_code(db)
    project = await repo.create(**data)
    await db.flush()

    if body.required_skills:
        skill_repo = _ProjSkillRepo(db)
        await skill_repo.set_skills(
            project_id=project.project_id,
            skills=[s.model_dump() for s in body.required_skills],
        )

    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.put(
    "/projects/{project_id}/with-skills",
    response_model=ProjectResponse,
)
async def update_project_with_skills(
    project_id: int,
    body: UpdateProjectWithSkillsRequest,
    _: dict = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update a project and optionally replace required_skills."""
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    updates = body.model_dump(exclude={"required_skills"}, exclude_none=True)
    if updates:
        project = await repo.update(project_id, **updates)

    if body.required_skills is not None:
        skill_repo = _ProjSkillRepo(db)
        await skill_repo.set_skills(
            project_id=project_id,
            skills=[s.model_dump() for s in body.required_skills],
        )

    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)
