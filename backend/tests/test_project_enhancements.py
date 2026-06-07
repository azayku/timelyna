"""Tests — spec 12c : améliorations projets.

Covers:
  12c.35 — generate_project_code() : format correct (5 lettres majuscules + tiret + 4 chiffres),
            unicité garantie sur plusieurs appels
  12c.36 — create_entry avec projet en statut 'draft' → 422
"""
from __future__ import annotations

import re
import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.employee import Employee
from app.utils.project_code import generate_project_code
from tests.conftest import make_client, make_employee, make_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _auth(employee: Employee) -> dict:
    token = create_access_token(
        {
            "sub": employee.email,
            "employee_id": employee.employee_id,
            "org_id": employee.org_id,
            "role": employee.role,
        }
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def admin(db: AsyncSession) -> Employee:
    uid = _uid()
    emp = await make_employee(db, email=f"admin-pe-{uid}@example.com", role="admin")
    await db.commit()
    return emp


# ===========================================================================
# 12c.35 — generate_project_code format & unicité
# ===========================================================================


def test_generate_project_code_format():
    """generate_project_code() doit retourner 5 lettres majuscules + tiret + 4 chiffres."""
    pattern = re.compile(r"^[A-Z]{5}-\d{4}$")
    for _ in range(50):
        code = generate_project_code()
        assert pattern.match(code), (
            f"Code '{code}' ne correspond pas au format XXXXX-NNNN"
        )


def test_generate_project_code_uniqueness():
    """Plusieurs appels successifs doivent produire des codes variés (pas toujours identiques)."""
    codes = {generate_project_code() for _ in range(100)}
    # Avec 26^5 * 10^4 combinaisons possibles, 100 appels ne devraient pas tous être identiques
    assert len(codes) > 1, "generate_project_code() semble toujours retourner la même valeur"


# ===========================================================================
# 12c.36 — create_entry avec projet en statut 'draft' → 422
# ===========================================================================


@pytest.mark.asyncio
async def test_create_entry_draft_project_blocked(
    client: AsyncClient, db: AsyncSession, admin: Employee
):
    """POST /timesheet/entries avec un projet en statut 'draft' → 422."""
    uid = _uid()

    # Créer un client et un projet en statut 'draft'
    cli = await make_client(db, name=f"Client-{uid}")
    await db.commit()

    project = await make_project(
        db,
        client_id=cli.client_id,
        manager_id=admin.employee_id,
        name=f"Draft Project {uid}",
        status="draft",
    )
    await db.commit()

    # Tenter de créer une entrée sur ce projet
    resp = await client.post(
        "/api/v1/employee/timesheet/entries",
        json={
            "project_id": project.project_id,
            "work_date": str(date.today()),
            "hours_worked": 4.0,
            "description": "Tentative sur projet draft",
            "task_type": "dev",
            "entry_type": "normal",
            "billable_flag": True,
        },
        headers=_auth(admin),
    )
    assert resp.status_code == 422, (
        f"Attendu 422 pour un projet en statut 'draft', reçu {resp.status_code}: {resp.text}"
    )
