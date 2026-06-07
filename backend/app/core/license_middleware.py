"""License middleware stub — validates org license on each request."""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class LicenseMiddleware:
    """Validates org license on each request. Stub: no-op in dev mode."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            request = Request(scope, receive, send)
            # In production: load license from DB, validate, inject into request.state
            # For now: pass through
        await self.app(scope, receive, send)
