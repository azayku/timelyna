"""Integration test fixtures — reuse the session-scoped engine from root conftest."""
from __future__ import annotations

# Integration tests use the root-level conftest.py (backend/tests/conftest.py)
# which provides: db, client, async_client, make_employee, make_client, make_project, make_entry
# No extra fixtures needed here — just re-export the shared helpers.
