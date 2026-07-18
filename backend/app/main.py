"""FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.manager import router as manager_router
from app.api.v1.timesheet import router as timesheet_router
from app.api.v1.projects import router as projects_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.exports import router as exports_router
from app.api.v1.invoicing import router as invoicing_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.absences import router as absences_router
from app.api.v1.finance import router as finance_router
from app.api.v1.timer import router as timer_router
from app.api.v1.entry_templates import router as entry_templates_router
from app.api.v1.mfa import router as mfa_router
from app.api.v1.imports import router as imports_router
from app.api.v1.setup import router as setup_router
from app.api.v1.emergency_contacts import router as emergency_contacts_router

app = FastAPI(title="Timelyna API", version="1.0.0")


# ── Global error handlers — never expose stack traces to clients ──────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: convert unhandled exceptions to clean 500 responses."""
    import logging
    logger = logging.getLogger("app.errors")

    # IntegrityError → 409 Conflict
    exc_name = type(exc).__name__
    exc_str = str(exc).lower()

    if "integrityerror" in exc_name.lower() or "unique constraint" in exc_str:
        logger.warning("IntegrityError on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=409,
            content={"detail": "Une saisie identique existe déjà pour ce projet, cette date et ce type d'heures."},
        )

    if "operationalerror" in exc_name.lower() or "no such column" in exc_str:
        logger.error("DB schema error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erreur de configuration de la base de données. Contactez l'administrateur."},
        )

    # Generic 500
    logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur est survenue. Veuillez réessayer ou contacter votre administrateur."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Accept-Language"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(manager_router, prefix="/api/v1")
app.include_router(timesheet_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(invoicing_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(absences_router, prefix="/api/v1")
app.include_router(finance_router, prefix="/api/v1")
app.include_router(timer_router, prefix="/api/v1")
app.include_router(entry_templates_router, prefix="/api/v1")
app.include_router(imports_router, prefix="/api/v1")
app.include_router(mfa_router, prefix="/api/v1")
app.include_router(setup_router, prefix="/api/v1")
app.include_router(emergency_contacts_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
