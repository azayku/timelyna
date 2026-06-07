"""JWT utilities, dependencies, and RBAC helpers."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

_bearer = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

def _load_or_generate_keys() -> tuple[Any, Any]:
    """Load RS256 keys from env or generate ephemeral ones for dev."""
    settings = get_settings()
    priv_pem = settings.AUTH_PRIVATE_KEY.replace("\\n", "\n").strip()
    pub_pem = settings.AUTH_PUBLIC_KEY.replace("\\n", "\n").strip()

    if priv_pem and pub_pem:
        private_key = serialization.load_pem_private_key(
            priv_pem.encode(), password=None, backend=default_backend()
        )
        public_key = serialization.load_pem_public_key(
            pub_pem.encode(), backend=default_backend()
        )
        return private_key, public_key

    # Ephemeral key for development / testing
    if settings.APP_ENV == "production":
        raise RuntimeError(
            "CRITICAL: AUTH_PRIVATE_KEY and AUTH_PUBLIC_KEY must be set in production. "
            "Generate keys with: ssh-keygen -t rsa -b 4096 -m PEM -f jwt.key && "
            "openssl rsa -in jwt.key -pubout -outform PEM -out jwt.key.pub"
        )
    
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    return private_key, private_key.public_key()


_PRIVATE_KEY, _PUBLIC_KEY = _load_or_generate_keys()


def get_public_key_pem() -> str:
    return _PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


def get_private_key_pem() -> str:
    return _PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


# ---------------------------------------------------------------------------
# Task 1.6 — create_access_token / decode_access_token
# ---------------------------------------------------------------------------

def create_access_token(data: dict) -> str:
    """Create a signed RS256 JWT access token."""
    settings = get_settings()
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update({
        "iat": now,
        "exp": now + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
    })
    return jwt.encode(payload, get_private_key_pem(), algorithm="RS256")


def decode_access_token(token: str) -> dict:
    """Decode and verify an RS256 JWT. Raises HTTPException on failure."""
    try:
        return jwt.decode(token, get_public_key_pem(), algorithms=["RS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Task 1.7 — get_current_user dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """FastAPI dependency: extract and validate Bearer JWT, return payload."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    # Inject proxy context if this is a proxy token
    if payload.get("is_proxy"):
        payload["proxy_admin_id"] = payload.get("proxy_admin_id")
    return payload


# ---------------------------------------------------------------------------
# Task 1.8 — require_role dependency factory
# ---------------------------------------------------------------------------

def require_role(*roles: str):
    """FastAPI dependency factory that enforces role-based access."""

    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "")
        # admin always has access
        if user_role == "admin" or user_role in roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return _check


# ---------------------------------------------------------------------------
# JWKS helpers (task 1.16)
# ---------------------------------------------------------------------------

import base64
import struct


def _int_to_base64url(n: int) -> str:
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()


def get_jwks() -> dict:
    """Return the RS256 public key as a JWKS document."""
    pub_numbers = _PUBLIC_KEY.public_key().public_numbers() if hasattr(_PUBLIC_KEY, "public_key") else _PUBLIC_KEY.public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": "timesheetpro-rs256-1",
                "n": _int_to_base64url(pub_numbers.n),
                "e": _int_to_base64url(pub_numbers.e),
            }
        ]
    }
