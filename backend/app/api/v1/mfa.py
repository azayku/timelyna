"""MFA/2FA management endpoints — /api/v1/mfa/..."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.employee import Employee
from app.services.mfa_service import MFAService

router = APIRouter(prefix="/mfa", tags=["MFA"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class MFASetupResponse(BaseModel):
    """Response for MFA setup initialization."""
    secret: str = Field(..., description="Base32-encoded TOTP secret (save this as backup)")
    qr_code_base64: str = Field(..., description="Base64-encoded PNG QR code for scanning")
    totp_uri: str = Field(..., description="otpauth:// URI for manual entry")


class MFAVerifyRequest(BaseModel):
    """Request body for TOTP code verification."""
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit TOTP code")


class MFAStatusResponse(BaseModel):
    """Response indicating MFA enablement status."""
    mfa_enabled: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Check if MFA is enabled for the current user."""
    result = await db.execute(
        select(Employee).where(Employee.employee_id == current_user["user_id"])
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    return MFAStatusResponse(mfa_enabled=bool(employee.mfa_enabled))


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate TOTP secret and QR code for MFA configuration.

    The user should scan the QR code with Google Authenticator / Authy,
    then call /mfa/enable with a valid TOTP code to activate MFA.
    """
    result = await db.execute(
        select(Employee).where(Employee.employee_id == current_user["user_id"])
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    svc = MFAService()
    secret = svc.generate_secret()

    # Store secret (not yet enabled)
    employee.mfa_secret = secret
    await db.commit()

    totp_uri = svc.get_totp_uri(secret, employee.email)
    qr_base64 = svc.generate_qr_base64(totp_uri)

    return MFASetupResponse(secret=secret, qr_code_base64=qr_base64, totp_uri=totp_uri)


@router.post("/enable", status_code=status.HTTP_200_OK)
async def enable_mfa(
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Enable MFA after verifying the TOTP code.

    Requires prior call to /mfa/setup to generate the secret.
    """
    result = await db.execute(
        select(Employee).where(Employee.employee_id == current_user["user_id"])
    )
    employee = result.scalar_one_or_none()
    if not employee or not employee.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA non configuré. Appelez /mfa/setup d'abord."
        )

    svc = MFAService()
    if not svc.verify_totp(employee.mfa_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invalide")

    employee.mfa_enabled = True
    await db.commit()
    return {"message": "MFA activé avec succès"}


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_mfa(
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Disable MFA after verifying the TOTP code.

    Clears the stored secret and sets mfa_enabled to False.
    """
    result = await db.execute(
        select(Employee).where(Employee.employee_id == current_user["user_id"])
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    if not employee.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA déjà désactivé")

    svc = MFAService()
    if not svc.verify_totp(employee.mfa_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invalide")

    employee.mfa_enabled = False
    employee.mfa_secret = None
    await db.commit()
    return {"message": "MFA désactivé"}


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_mfa(
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Verify a TOTP code for an already-enabled MFA user.

    Used during login flow (2-step authentication).
    """
    result = await db.execute(
        select(Employee).where(Employee.employee_id == current_user["user_id"])
    )
    employee = result.scalar_one_or_none()
    if not employee or not employee.mfa_enabled or not employee.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA non activé")

    svc = MFAService()
    if not svc.verify_totp(employee.mfa_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide ou expiré"
        )

    return {"message": "Code vérifié", "valid": True}
