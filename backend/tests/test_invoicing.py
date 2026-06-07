"""Tests for invoicing — tasks 5.9, 5.10, 5.11."""
from __future__ import annotations

import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.timesheet_entry import TimesheetEntry
from app.services.invoicing_service import InvoicingService
from tests.conftest import make_client, make_employee, make_entry, make_project


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _auth(employee) -> dict:
    token = create_access_token({
        "sub": employee.email,
        "employee_id": employee.employee_id,
        "org_id": employee.org_id,
        "role": employee.role,
    })
    return {"Authorization": f"Bearer {token}"}


async def _approve_entries(db: AsyncSession, employee_id: int, project_id: int) -> None:
    """Mark all draft/submitted entries for employee+project as approved."""
    await db.execute(
        update(TimesheetEntry)
        .where(
            TimesheetEntry.employee_id == employee_id,
            TimesheetEntry.project_id == project_id,
            TimesheetEntry.deleted_at.is_(None),
        )
        .values(status="approved")
    )
    await db.flush()


# ---------------------------------------------------------------------------
# 5.9 — Unit tests: create_draft
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_draft_no_entries(db: AsyncSession):
    """create_draft raises 400 when no approved entries exist for client+period."""
    uid = _uid()
    manager = await make_employee(db, email=f"mgr-{uid}@example.com", role="manager")
    cli = await make_client(db, name=f"Client-{uid}")
    await db.commit()

    svc = InvoicingService(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.create_draft(client_id=cli.client_id, period="2025-03")
    assert exc_info.value.status_code == 400
    assert "No approved entries" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_draft_success(db: AsyncSession):
    """create_draft creates invoice with correct line items and totals."""
    uid = _uid()
    manager = await make_employee(db, email=f"mgr-{uid}@example.com", role="manager")
    emp = await make_employee(db, email=f"emp-{uid}@example.com", role="employee", manager_id=manager.employee_id)
    cli = await make_client(db, name=f"Client-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    await db.commit()

    # Create entries in March 2025 and approve them
    entry1 = await make_entry(db, emp.employee_id, proj.project_id, date(2025, 3, 10), hours=8.0)
    entry2 = await make_entry(db, emp.employee_id, proj.project_id, date(2025, 3, 11), hours=4.0)
    await _approve_entries(db, emp.employee_id, proj.project_id)
    await db.commit()

    svc = InvoicingService(db)
    result = await svc.create_draft(
        client_id=cli.client_id,
        period="2025-03",
        created_by=manager.employee_id,
    )

    assert result["status"] == "draft"
    assert result["client_id"] == cli.client_id
    assert result["period"] == "2025-03"
    assert result["invoice_number"].startswith("FAC-")  # Format: FAC-YYYY-NNNN

    # Line items: one project, 12 hours total
    assert len(result["line_items"]) == 1
    li = result["line_items"][0]
    assert li["project_id"] == proj.project_id
    assert li["hours"] == 12.0
    assert li["rate"] == float(proj.billing_rate)
    expected_subtotal = 12.0 * float(proj.billing_rate)
    assert abs(li["subtotal"] - expected_subtotal) < 0.01

    # Totals
    assert abs(result["total_hours"] - 12.0) < 0.01
    assert abs(result["total_amount"] - expected_subtotal) < 0.01
    expected_tax = expected_subtotal * 20.0 / 100.0
    assert abs(result["tax_amount"] - expected_tax) < 0.01


@pytest.mark.asyncio
async def test_create_draft_excludes_non_approved(db: AsyncSession):
    """create_draft only includes approved entries, not draft or submitted ones."""
    uid = _uid()
    manager = await make_employee(db, email=f"mgr2-{uid}@example.com", role="manager")
    emp = await make_employee(db, email=f"emp2-{uid}@example.com", role="employee", manager_id=manager.employee_id)
    cli = await make_client(db, name=f"Client2-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    await db.commit()

    # Create a draft entry (not approved)
    await make_entry(db, emp.employee_id, proj.project_id, date(2025, 4, 1), hours=8.0)
    await db.commit()

    svc = InvoicingService(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.create_draft(client_id=cli.client_id, period="2025-04")
    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# 5.10 — Unit tests: finalize
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finalize_success(db: AsyncSession):
    """finalize sets invoice status to 'ready' and marks entries as 'invoiced'."""
    uid = _uid()
    manager = await make_employee(db, email=f"mgr3-{uid}@example.com", role="manager")
    emp = await make_employee(db, email=f"emp3-{uid}@example.com", role="employee", manager_id=manager.employee_id)
    cli = await make_client(db, name=f"Client3-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    await db.commit()

    entry = await make_entry(db, emp.employee_id, proj.project_id, date(2025, 5, 15), hours=6.0)
    await _approve_entries(db, emp.employee_id, proj.project_id)
    await db.commit()

    svc = InvoicingService(db)
    invoice = await svc.create_draft(client_id=cli.client_id, period="2025-05")
    result = await svc.finalize(invoice["invoice_id"])

    assert result["status"] == "ready"

    # Verify entry is now 'invoiced'
    await db.refresh(entry)
    assert entry.status == "invoiced"


@pytest.mark.asyncio
async def test_finalize_wrong_status(db: AsyncSession):
    """finalize raises 409 when invoice is not in 'draft' status."""
    uid = _uid()
    manager = await make_employee(db, email=f"mgr4-{uid}@example.com", role="manager")
    emp = await make_employee(db, email=f"emp4-{uid}@example.com", role="employee", manager_id=manager.employee_id)
    cli = await make_client(db, name=f"Client4-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    await db.commit()

    await make_entry(db, emp.employee_id, proj.project_id, date(2025, 6, 10), hours=8.0)
    await _approve_entries(db, emp.employee_id, proj.project_id)
    await db.commit()

    svc = InvoicingService(db)
    invoice = await svc.create_draft(client_id=cli.client_id, period="2025-06")
    # Finalize once → status becomes 'ready'
    await svc.finalize(invoice["invoice_id"])

    # Try to finalize again → 409
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await svc.finalize(invoice["invoice_id"])
    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 5.11 — Integration test: create → finalize → entries immutable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_integration_invoiced_entry_cannot_be_edited(db: AsyncSession, client):
    """After finalize, invoiced entries cannot be edited via the API (403)."""
    uid = _uid()
    manager = await make_employee(db, email=f"mgr5-{uid}@example.com", role="manager")
    emp = await make_employee(db, email=f"emp5-{uid}@example.com", role="employee", manager_id=manager.employee_id)
    finance = await make_employee(db, email=f"fin5-{uid}@example.com", role="finance")
    cli = await make_client(db, name=f"Client5-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    await db.commit()

    # Create and approve an entry
    entry = await make_entry(db, emp.employee_id, proj.project_id, date(2025, 7, 14), hours=8.0)
    await _approve_entries(db, emp.employee_id, proj.project_id)
    await db.commit()

    # Create draft invoice
    svc = InvoicingService(db)
    invoice = await svc.create_draft(client_id=cli.client_id, period="2025-07")

    # Finalize → entries become 'invoiced'
    await svc.finalize(invoice["invoice_id"])

    # Verify entry is invoiced
    await db.refresh(entry)
    assert entry.status == "invoiced"

    # Try to edit the invoiced entry via API → should get 403
    resp = await client.put(
        f"/api/v1/employee/timesheet/entries/{entry.timesheet_entry_id}",
        json={"description": "Trying to edit invoiced entry"},
        headers=_auth(emp),
    )
    assert resp.status_code == 403
