"""Tests: generate_project_code et ensure_unique_project_code (spec 12c.35)."""
from __future__ import annotations

import re

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.project_code import generate_project_code, ensure_unique_project_code


# ---------------------------------------------------------------------------
# Format test
# ---------------------------------------------------------------------------

def test_generate_project_code_format():
    """generate_project_code() doit retourner XXXXX-NNNN."""
    pattern = re.compile(r"^[A-Z]{5}-\d{4}$")
    for _ in range(50):
        code = generate_project_code()
        assert pattern.match(code), f"Code invalide: {code}"


def test_generate_project_code_randomness():
    """Deux appels successifs ne doivent pas toujours retourner le même code."""
    codes = {generate_project_code() for _ in range(20)}
    # With 26^5 * 10^4 = ~11.8M possibilities, 20 draws should almost never collide
    assert len(codes) > 1


# ---------------------------------------------------------------------------
# Unicité test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ensure_unique_project_code_returns_unused(db: AsyncSession):
    """ensure_unique_project_code retourne un code absent de la DB."""
    code = await ensure_unique_project_code(db)
    pattern = re.compile(r"^[A-Z]{5}-\d{4}$")
    assert pattern.match(code), f"Code invalide: {code}"

    # Verify it doesn't exist in DB
    from app.repositories.project_repository import ProjectRepository
    repo = ProjectRepository(db)
    existing = await repo.get_by_code(code)
    assert existing is None


@pytest.mark.asyncio
async def test_ensure_unique_project_code_avoids_existing(db: AsyncSession):
    """ensure_unique_project_code ne retourne pas un code déjà utilisé."""
    from tests.conftest import make_client, make_project

    # Create a project with a known code
    cli = await make_client(db, name="CodeTestClient")
    import bcrypt as _bcrypt
    from app.models.employee import Employee
    mgr = Employee(
        email="mgr_code@example.com",
        first_name="Mgr",
        last_name="Code",
        password_hash=_bcrypt.hashpw(b"pw", _bcrypt.gensalt(rounds=4)).decode(),
        role="manager",
        employment_status="active",
        org_id=1,
    )
    db.add(mgr)
    await db.flush()
    await db.refresh(mgr)

    proj = await make_project(db, client_id=cli.client_id, manager_id=mgr.employee_id)
    await db.commit()

    # The generated code should not match the existing project code
    generated = await ensure_unique_project_code(db)
    assert generated != proj.project_code
