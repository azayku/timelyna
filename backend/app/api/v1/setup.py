"""Setup wizard endpoint — only accessible when the app is not yet installed."""
from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/setup", tags=["setup"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SetupStatusResponse(BaseModel):
    is_installed: bool
    app_name: str


class AppConfigResponse(BaseModel):
    """Response containing app branding and configuration."""
    app_name: str
    company_name: str | None
    company_logo: str | None


class SetupPayload(BaseModel):
    # Organisation / branding
    company_name: str
    app_name: str = "Timelyna"
    company_logo: str | None = None  # base64 data-URL or empty

    # Admin account
    admin_email: EmailStr
    admin_first_name: str
    admin_last_name: str
    admin_password: str

    @field_validator("admin_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit comporter au moins 8 caractères")
        return v

    @field_validator("company_name", "admin_first_name", "admin_last_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ce champ ne peut pas être vide")
        return v.strip()


class SetupResponse(BaseModel):
    message: str
    company_name: str
    app_name: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_config(db: AsyncSession):
    """Return the single AppConfig row, creating it if absent."""
    from app.models.app_config import AppConfig
    result = await db.execute(select(AppConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = AppConfig(is_installed=False, app_name="Timelyna")
        db.add(cfg)
        await db.flush()
    return cfg


# ---------------------------------------------------------------------------
# GET /api/v1/setup/status
# ---------------------------------------------------------------------------

@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(db: AsyncSession = Depends(get_db)) -> SetupStatusResponse:
    """Public endpoint — tells the frontend whether the wizard must be shown."""
    cfg = await _get_config(db)
    return SetupStatusResponse(is_installed=cfg.is_installed, app_name=cfg.app_name)


# ---------------------------------------------------------------------------
# GET /api/v1/setup/config
# ---------------------------------------------------------------------------

@router.get("/config", response_model=AppConfigResponse)
async def get_app_config(db: AsyncSession = Depends(get_db)) -> AppConfigResponse:
    """Public endpoint — returns the app branding and configuration."""
    cfg = await _get_config(db)
    return AppConfigResponse(
        app_name=cfg.app_name,
        company_name=cfg.company_name,
        company_logo=cfg.company_logo,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/setup
# ---------------------------------------------------------------------------

@router.post("", response_model=SetupResponse, status_code=status.HTTP_201_CREATED)
async def run_setup(
    payload: SetupPayload,
    db: AsyncSession = Depends(get_db),
) -> SetupResponse:
    """
    One-time setup wizard.

    - Creates the admin employee account
    - Creates / updates the default organisation
    - Marks the app as installed in app_config
    
    Returns 409 if already installed.
    """
    from app.models.app_config import AppConfig
    from app.models.employee import Employee
    from app.models.organization import Organization
    from app.models.org_settings import OrgSettings

    cfg = await _get_config(db)

    if cfg.is_installed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'application est déjà installée.",
        )

    # ------------------------------------------------------------------
    # 1. Check no admin already exists
    # ------------------------------------------------------------------
    existing = await db.execute(
        select(Employee).where(
            Employee.email == payload.admin_email,
            Employee.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )

    # ------------------------------------------------------------------
    # 2. Validate & store logo
    # ------------------------------------------------------------------
    logo: str | None = None
    if payload.company_logo:
        raw = payload.company_logo.strip()
        # Accept data-URL (data:image/...;base64,...) or plain base64
        if raw.startswith("data:"):
            # Validate structure
            if not re.match(r"^data:image/(png|jpeg|jpg|gif|svg\+xml|webp);base64,", raw):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Format de logo invalide. Utilisez PNG, JPEG, GIF ou WebP.",
                )
            # Rough size check (base64 ≈ 4/3 of binary)
            b64_part = raw.split(",", 1)[-1]
            approx_bytes = len(b64_part) * 3 // 4
            if approx_bytes > 2 * 1024 * 1024:  # 2 MB max
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Le logo ne doit pas dépasser 2 Mo.",
                )
            # Validate base64
            try:
                base64.b64decode(b64_part, validate=True)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Données base64 invalides.",
                )
            logo = raw
        elif raw:
            logo = raw  # plain URL

    # ------------------------------------------------------------------
    # 3. Create / update default organisation (org_id = 1)
    # ------------------------------------------------------------------
    org_result = await db.execute(
        select(Organization).where(Organization.org_id == 1)
    )
    org = org_result.scalar_one_or_none()
    if org is None:
        org = Organization(org_id=1, org_name=payload.company_name)
        db.add(org)
        await db.flush()
    else:
        org.org_name = payload.company_name

    # ------------------------------------------------------------------
    # 4. Update org_settings name
    # ------------------------------------------------------------------
    settings_result = await db.execute(
        select(OrgSettings).where(OrgSettings.org_id == 1)
    )
    org_settings = settings_result.scalar_one_or_none()
    if org_settings is None:
        org_settings = OrgSettings(org_id=1, org_name=payload.company_name)
        db.add(org_settings)
        await db.flush()
    else:
        org_settings.org_name = payload.company_name

    # Store logo in org_settings if column exists
    try:
        org_settings.company_logo = logo  # type: ignore[attr-defined]
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 5. Create admin employee
    # ------------------------------------------------------------------
    pw_hash = bcrypt.hashpw(
        payload.admin_password.encode(), bcrypt.gensalt()
    ).decode()

    # Generate a unique username from name
    base_username = (
        payload.admin_first_name[:1].lower() + payload.admin_last_name.lower()
    ).replace(" ", "")[:20]

    admin = Employee(
        email=payload.admin_email,
        first_name=payload.admin_first_name,
        last_name=payload.admin_last_name,
        role="admin",
        employment_status="active",
        org_id=1,
        username=base_username,
        password_hash=pw_hash,
        must_change_password=False,
    )
    db.add(admin)
    await db.flush()

    # Link org manager
    org.manager_id = admin.employee_id

    # ------------------------------------------------------------------
    # 6. Mark as installed
    # ------------------------------------------------------------------
    cfg.is_installed = True
    cfg.company_name = payload.company_name
    cfg.app_name = payload.app_name.strip() or "Timelyna"
    cfg.company_logo = logo
    cfg.installed_at = datetime.now(timezone.utc)

    await db.commit()

    logger.info(
        "Setup completed: company=%s, admin=%s",
        payload.company_name,
        payload.admin_email,
    )

    return SetupResponse(
        message="Installation terminée avec succès.",
        company_name=payload.company_name,
        app_name=cfg.app_name,
    )
