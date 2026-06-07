"""Utilities for generating unique project codes."""
from __future__ import annotations

import random
import string


def generate_project_code() -> str:
    """Generate a project code in the format XXXXX-NNNN (5 uppercase letters + 4 digits)."""
    letters = "".join(random.choices(string.ascii_uppercase, k=5))
    digits = "".join(random.choices(string.digits, k=4))
    return f"{letters}-{digits}"


async def ensure_unique_project_code(db) -> str:
    """Generate a project code guaranteed to be unique in the DB."""
    from app.repositories.project_repository import ProjectRepository

    repo = ProjectRepository(db)
    for _ in range(20):
        code = generate_project_code()
        if not await repo.get_by_code(code):
            return code
    raise ValueError("Cannot generate unique project code after 20 attempts")
