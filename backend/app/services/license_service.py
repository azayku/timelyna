"""License validation service."""
from __future__ import annotations

import time
from typing import Any

import jwt

from app.core.config import get_settings
from app.core.license_errors import (
    LicenseExpiredError,
    LicenseInvalidError,
    LicenseRevokedError,
)


class LicenseService:
    def __init__(self) -> None:
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Task 6.3 — local validation
    # ------------------------------------------------------------------

    def validate_local(self, token: str, public_key_pem: str | None = None) -> dict:
        """Decode and verify license JWT locally using LICENSE_PUBLIC_KEY.

        Returns decoded payload if valid.
        Raises LicenseError on: invalid signature, expired (past grace), revoked.

        Grace period: if exp < now but grace > now → still valid (degraded mode).
        """
        pub_key = public_key_pem or self.settings.LICENSE_PUBLIC_KEY
        if not pub_key:
            raise LicenseInvalidError("No public key configured")

        try:
            payload = jwt.decode(
                token,
                pub_key,
                algorithms=["RS256"],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError as exc:
            raise LicenseInvalidError(str(exc)) from exc

        if payload.get("revoked"):
            raise LicenseRevokedError("License has been revoked")

        now = int(time.time())
        exp = payload.get("exp", 0)
        grace = payload.get("grace", exp)

        if now > grace:
            raise LicenseExpiredError("License has expired (past grace period)")

        return payload

    # ------------------------------------------------------------------
    # Task 6.4 — remote validation (stub)
    # ------------------------------------------------------------------

    async def validate_remote(self, org_id: str, api_key: str, token: str) -> bool:
        """POST to publisher phone-home endpoint. Returns True if valid.
        Stub: always returns True unless token payload has revoked=True.
        """
        try:
            payload = self._decode_without_verify(token)
            return not payload.get("revoked", False)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Task 6.5 — Redis caching stubs
    # ------------------------------------------------------------------

    def get_cached_validation(self, org_id: str) -> dict | None:
        """Check Redis cache. Returns cached result or None. Stub: always None in tests."""
        return None

    def cache_validation(self, org_id: str, result: dict, ttl_seconds: int = 86400) -> None:
        """Cache validation result in Redis. Stub: no-op in tests."""
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _decode_without_verify(self, token: str) -> dict:
        """Decode JWT without any verification (for stub remote calls)."""
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
            algorithms=["RS256"],
        )
