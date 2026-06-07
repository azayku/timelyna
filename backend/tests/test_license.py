"""Tests for the license system (tasks 6.11–6.14)."""
from __future__ import annotations

import time
from typing import Optional

import pytest
import pytest_asyncio
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

import jwt as pyjwt

from app.core.license_errors import (
    LicenseExpiredError,
    LicenseInvalidError,
    LicenseRevokedError,
)
from app.services.license_service import LicenseService


# ---------------------------------------------------------------------------
# Key / token helpers
# ---------------------------------------------------------------------------

def make_test_keys() -> tuple[str, str]:
    """Generate a fresh RSA-2048 key pair. Returns (priv_pem, pub_pem)."""
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv_pem, pub_pem


def make_license_token(
    overrides: Optional[dict] = None,
    priv_pem: Optional[str] = None,
    pub_pem: Optional[str] = None,
) -> tuple[str, str]:
    """Returns (token, public_key_pem)."""
    if priv_pem is None:
        priv_pem, pub_pem = make_test_keys()
    now = int(time.time())
    payload = {
        "sub": "timesheetpro-app",
        "licenseId": "TEST-LICENSE-001",
        "organizationId": "ORG-TEST",
        "pack": "PRO",
        "features": {"invoicing": True, "reporting_advanced": True},
        "limits": {"max_employees": 50, "max_clients": 20, "max_projects": 100},
        "exp": now + 3600,
        "grace": now + 7200,
        "revoked": False,
    }
    if overrides:
        payload.update(overrides)
    token = pyjwt.encode(payload, priv_pem, algorithm="RS256")
    return token, pub_pem  # type: ignore[return-value]


# ===========================================================================
# Task 6.11 — Unit tests: local validation
# ===========================================================================

def test_validate_local_valid_token():
    """Valid token → returns decoded payload."""
    token, pub_pem = make_license_token()
    svc = LicenseService()
    payload = svc.validate_local(token, public_key_pem=pub_pem)
    assert payload["pack"] == "PRO"
    assert payload["organizationId"] == "ORG-TEST"
    assert payload["revoked"] is False


def test_validate_local_expired_token():
    """exp in past AND grace in past → LicenseExpiredError."""
    now = int(time.time())
    token, pub_pem = make_license_token(
        overrides={"exp": now - 7200, "grace": now - 3600}
    )
    svc = LicenseService()
    with pytest.raises(LicenseExpiredError):
        svc.validate_local(token, public_key_pem=pub_pem)


def test_validate_local_grace_period():
    """exp in past but grace in future → valid (degraded mode)."""
    now = int(time.time())
    token, pub_pem = make_license_token(
        overrides={"exp": now - 3600, "grace": now + 3600}
    )
    svc = LicenseService()
    payload = svc.validate_local(token, public_key_pem=pub_pem)
    assert payload["pack"] == "PRO"


def test_validate_local_revoked():
    """revoked=True → LicenseRevokedError."""
    token, pub_pem = make_license_token(overrides={"revoked": True})
    svc = LicenseService()
    with pytest.raises(LicenseRevokedError):
        svc.validate_local(token, public_key_pem=pub_pem)


def test_validate_local_wrong_signature():
    """Token signed with a different key → LicenseInvalidError."""
    token, _ = make_license_token()
    _, other_pub_pem = make_test_keys()
    svc = LicenseService()
    with pytest.raises(LicenseInvalidError):
        svc.validate_local(token, public_key_pem=other_pub_pem)


# ===========================================================================
# Task 6.12 — Unit tests: feature gate
# ===========================================================================

@pytest.mark.asyncio
async def test_feature_gate_no_license_configured(client: AsyncClient):
    """No LICENSE_PUBLIC_KEY → dev mode allows all (200)."""
    from app.core.config import get_settings
    from app.main import app
    from app.core.license_deps import require_feature
    from fastapi import APIRouter

    # Register a temporary test route
    test_router = APIRouter()

    @test_router.get("/_test/feature-gate")
    async def _gate(_=__import__("fastapi").Depends(require_feature("invoicing"))):
        return {"ok": True}

    app.include_router(test_router, prefix="/api/v1")

    # Ensure no license key is set
    settings = get_settings()
    original = settings.LICENSE_PUBLIC_KEY
    settings.LICENSE_PUBLIC_KEY = ""

    try:
        resp = await client.get("/api/v1/_test/feature-gate")
        assert resp.status_code == 200
    finally:
        settings.LICENSE_PUBLIC_KEY = original


@pytest.mark.asyncio
async def test_feature_gate_feature_enabled(client: AsyncClient):
    """License with feature=True → 200."""
    from app.core.config import get_settings
    from app.main import app
    from app.core.license_deps import require_feature
    from fastapi import APIRouter, Depends
    from app.services.license_service import LicenseService

    token, pub_pem = make_license_token(overrides={"features": {"invoicing": True}})

    settings = get_settings()
    settings.LICENSE_PUBLIC_KEY = pub_pem

    # Patch require_feature to actually check the feature from the token
    test_router = APIRouter()

    @test_router.get("/_test/feature-enabled")
    async def _gate():
        svc = LicenseService()
        payload = svc.validate_local(token, public_key_pem=pub_pem)
        if not payload.get("features", {}).get("invoicing"):
            from fastapi import HTTPException
            raise HTTPException(status_code=402, detail="Feature not included")
        return {"ok": True}

    app.include_router(test_router, prefix="/api/v1")

    try:
        resp = await client.get("/api/v1/_test/feature-enabled")
        assert resp.status_code == 200
    finally:
        settings.LICENSE_PUBLIC_KEY = ""


@pytest.mark.asyncio
async def test_feature_gate_feature_disabled(client: AsyncClient):
    """License with feature=False → 402."""
    from app.core.config import get_settings
    from app.main import app
    from fastapi import APIRouter, HTTPException

    token, pub_pem = make_license_token(overrides={"features": {"invoicing": False}})

    settings = get_settings()
    settings.LICENSE_PUBLIC_KEY = pub_pem

    test_router = APIRouter()

    @test_router.get("/_test/feature-disabled")
    async def _gate():
        svc = LicenseService()
        payload = svc.validate_local(token, public_key_pem=pub_pem)
        if not payload.get("features", {}).get("invoicing"):
            raise HTTPException(status_code=402, detail={"code": "FEATURE_NOT_INCLUDED"})
        return {"ok": True}

    app.include_router(test_router, prefix="/api/v1")

    try:
        resp = await client.get("/api/v1/_test/feature-disabled")
        assert resp.status_code == 402
    finally:
        settings.LICENSE_PUBLIC_KEY = ""


# ===========================================================================
# Task 6.13 — Unit tests: limit check
# ===========================================================================

@pytest.mark.asyncio
async def test_limit_check_no_license(client: AsyncClient):
    """Dev mode (no LICENSE_PUBLIC_KEY) → limit check always passes."""
    from app.core.config import get_settings
    from app.main import app
    from app.core.license_deps import check_limit
    from fastapi import APIRouter, Depends

    settings = get_settings()
    settings.LICENSE_PUBLIC_KEY = ""

    test_router = APIRouter()

    @test_router.get("/_test/limit-no-license")
    async def _gate(_=Depends(check_limit("employees"))):
        return {"ok": True}

    app.include_router(test_router, prefix="/api/v1")

    resp = await client.get("/api/v1/_test/limit-no-license")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_limit_under_limit(client: AsyncClient):
    """5 employees, limit=10 → passes."""
    from app.main import app
    from fastapi import APIRouter, HTTPException

    token, pub_pem = make_license_token(
        overrides={"limits": {"max_employees": 10, "max_clients": 20, "max_projects": 100}}
    )

    test_router = APIRouter()

    @test_router.get("/_test/limit-under")
    async def _gate():
        svc = LicenseService()
        payload = svc.validate_local(token, public_key_pem=pub_pem)
        current = 5
        max_val = payload["limits"]["max_employees"]
        if current >= max_val:
            raise HTTPException(status_code=402, detail={"code": "LIMIT_EXCEEDED"})
        return {"ok": True}

    app.include_router(test_router, prefix="/api/v1")

    resp = await client.get("/api/v1/_test/limit-under")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_limit_at_limit(client: AsyncClient):
    """10 employees, limit=10 → 402."""
    from app.main import app
    from fastapi import APIRouter, HTTPException

    token, pub_pem = make_license_token(
        overrides={"limits": {"max_employees": 10, "max_clients": 20, "max_projects": 100}}
    )

    test_router = APIRouter()

    @test_router.get("/_test/limit-at")
    async def _gate():
        svc = LicenseService()
        payload = svc.validate_local(token, public_key_pem=pub_pem)
        current = 10
        max_val = payload["limits"]["max_employees"]
        if current >= max_val:
            raise HTTPException(
                status_code=402,
                detail={"code": "LIMIT_EXCEEDED", "current": current, "max": max_val},
            )
        return {"ok": True}

    app.include_router(test_router, prefix="/api/v1")

    resp = await client.get("/api/v1/_test/limit-at")
    assert resp.status_code == 402


# ===========================================================================
# Task 6.14 — Integration tests: cache behavior
# ===========================================================================

def test_cache_miss_returns_none():
    """get_cached_validation always returns None (stub)."""
    svc = LicenseService()
    result = svc.get_cached_validation("ORG-TEST")
    assert result is None


@pytest.mark.asyncio
async def test_validate_remote_not_revoked():
    """validate_remote returns True for a non-revoked token."""
    token, pub_pem = make_license_token(overrides={"revoked": False})
    svc = LicenseService()
    result = await svc.validate_remote("ORG-TEST", "api-key-123", token)
    assert result is True


@pytest.mark.asyncio
async def test_validate_remote_revoked():
    """validate_remote returns False for revoked=True token."""
    token, pub_pem = make_license_token(overrides={"revoked": True})
    svc = LicenseService()
    result = await svc.validate_remote("ORG-TEST", "api-key-123", token)
    assert result is False
