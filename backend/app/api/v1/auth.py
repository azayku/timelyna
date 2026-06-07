"""Auth route handlers — /api/v1/auth/..."""
from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import get_current_user, get_jwks
from app.core.limiter import login_limiter, password_reset_limiter
from fastapi_limiter.depends import RateLimiter

settings = get_settings()
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetBody,
    PasswordResetRequestBody,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_NAME = "refresh_token"
_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str, max_age: int = 30 * 24 * 3600) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        path=_COOKIE_PATH,
        max_age=max_age,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path=_COOKIE_PATH)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(limiter=login_limiter))],
)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    ip = request.client.host if request.client else None
    svc = AuthService(db)
    tokens = await svc.authenticate(body.identifier, body.password, ip_address=ip)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"])


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: Optional[str] = Cookie(default=None, alias=_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    if refresh_token:
        svc = AuthService(db)
        await svc.revoke_token(refresh_token)
    _clear_refresh_cookie(response)
    return response


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None, alias=_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    svc = AuthService(db)
    tokens = await svc.refresh(refresh_token)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"])


# ---------------------------------------------------------------------------
# POST /password/change
# ---------------------------------------------------------------------------

@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = AuthService(db)
    await svc.change_password(
        current_user["employee_id"], body.current_password, body.new_password
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# POST /password/reset-request
# ---------------------------------------------------------------------------

@router.post(
    "/password/reset-request",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(limiter=password_reset_limiter))],
)
async def password_reset_request(
    request: Request,
    body: PasswordResetRequestBody,
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AuthService(db)
    await svc.request_reset(body.email)
    return {"detail": "If that email exists, a reset link has been sent."}


# ---------------------------------------------------------------------------
# POST /password/reset
# ---------------------------------------------------------------------------

@router.post(
    "/password/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(limiter=password_reset_limiter))],
)
async def password_reset(
    request: Request,
    body: PasswordResetBody,
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = AuthService(db)
    await svc.reset_password(body.token, body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Task 1.16 — GET /.well-known/jwks.json
# ---------------------------------------------------------------------------

@router.get("/.well-known/jwks.json", include_in_schema=True)
async def jwks() -> dict:
    return get_jwks()


# ---------------------------------------------------------------------------
# GET /auth/org-config — Public org configuration for authenticated users
# ---------------------------------------------------------------------------

@router.get("/org-config")
async def get_org_config(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return public organization configuration (next_week_display_day, etc.)"""
    from app.models.org_settings import OrgSettings
    from sqlalchemy import select
    
    org_id = current_user.get("org_id", 1)
    result = await db.execute(select(OrgSettings).where(OrgSettings.org_id == org_id))
    s = result.scalar_one_or_none()
    
    if not s:
        return {"next_week_display_day": 2}  # Default: Tuesday
    
    return {"next_week_display_day": s.next_week_display_day}
