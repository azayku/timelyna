"""Tests for US-6: approval/rejection emails in employee's preferred language."""
from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval
from app.models.organization import Organization
from app.repositories.timesheet_repository import TimesheetRepository
from app.services.approval_service import ApprovalService
from app.tasks.notification_tasks import _approval_template, _resolve_lang
from tests.conftest import make_client, make_employee, make_entry, make_project


def _uid() -> str:
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

def test_resolve_lang_fr():
    assert _resolve_lang("fr") == "fr"


def test_resolve_lang_en():
    assert _resolve_lang("en") == "en"


def test_resolve_lang_it():
    assert _resolve_lang("it") == "it"


def test_resolve_lang_unknown_falls_back_to_fr():
    assert _resolve_lang("xx") == "fr"
    assert _resolve_lang(None) == "fr"
    assert _resolve_lang("") == "fr"
    assert _resolve_lang("zh") == "fr"


def test_approval_template_approved_fr():
    assert _approval_template("approved", "fr") == "approval_approved_fr"


def test_approval_template_approved_en():
    assert _approval_template("approved", "en") == "approval_approved_en"


def test_approval_template_approved_it():
    assert _approval_template("approved", "it") == "approval_approved_it"


def test_approval_template_rejected_fr():
    assert _approval_template("rejected", "fr") == "approval_rejected_fr"


def test_approval_template_rejected_en():
    assert _approval_template("rejected", "en") == "approval_rejected_en"


def test_approval_template_rejected_it():
    assert _approval_template("rejected", "it") == "approval_rejected_it"


def test_approval_template_unknown_lang_falls_back_to_fr():
    assert _approval_template("approved", "xx") == "approval_approved_fr"


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def approval_setup(db: AsyncSession):
    uid = _uid()

    # Create an organization with the manager as manager_id
    org = Organization(
        org_name=f"Org-{uid}",
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)

    manager = await make_employee(db, email=f"mgr-{uid}@example.com", role="manager")
    manager.org_id = org.org_id
    await db.flush()

    # Set the manager as org.manager_id
    org.manager_id = manager.employee_id
    await db.flush()

    emp = await make_employee(
        db,
        email=f"emp-{uid}@example.com",
        role="employee",
        manager_id=manager.employee_id,
    )
    emp.org_id = org.org_id
    await db.flush()

    cli = await make_client(db, name=f"Client-{uid}")
    proj = await make_project(db, client_id=cli.client_id, manager_id=manager.employee_id)
    await db.commit()

    return {"manager": manager, "emp": emp, "proj": proj, "org": org}


async def _submit_week(db: AsyncSession, emp, proj, week_start: date) -> int:
    entry = await make_entry(db, emp.employee_id, proj.project_id, week_start)
    await db.commit()
    ts_repo = TimesheetRepository(db)
    approval = await ts_repo.create_approval(emp.employee_id, emp.manager_id, week_start)
    await ts_repo.submit_week_entries(emp.employee_id, week_start, week_start)
    await db.commit()
    return approval.approval_id


# ---------------------------------------------------------------------------
# (a) Approval with lang='fr' → French template called
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_sends_fr_template(db: AsyncSession, approval_setup):
    emp = approval_setup["emp"]
    manager = approval_setup["manager"]
    proj = approval_setup["proj"]

    emp.preferred_language = "fr"
    await db.flush()
    await db.commit()

    week_start = date(2025, 1, 6)
    approval_id = await _submit_week(db, emp, proj, week_start)

    with patch(
        "app.services.approval_service.task_send_approval_notification"
    ) as mock_task:
        svc = ApprovalService(db)
        result = await svc.approve(manager.employee_id, approval_id)

    assert result["status"] == "approved"
    mock_task.assert_called_once()
    call_kwargs = mock_task.call_args
    # Accept both positional and keyword arguments
    args, kwargs = call_kwargs
    lang_passed = kwargs.get("lang") or (args[4] if len(args) > 4 else None)
    assert lang_passed == "fr", f"Expected lang='fr', got {lang_passed!r}"

    # Verify the template that would be used
    assert _approval_template("approved", lang_passed) == "approval_approved_fr"


# ---------------------------------------------------------------------------
# (b) Approval with lang='en' → English template called
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_sends_en_template(db: AsyncSession, approval_setup):
    emp = approval_setup["emp"]
    manager = approval_setup["manager"]
    proj = approval_setup["proj"]

    emp.preferred_language = "en"
    await db.flush()
    await db.commit()

    week_start = date(2025, 1, 13)
    approval_id = await _submit_week(db, emp, proj, week_start)

    with patch(
        "app.services.approval_service.task_send_approval_notification"
    ) as mock_task:
        svc = ApprovalService(db)
        result = await svc.approve(manager.employee_id, approval_id)

    assert result["status"] == "approved"
    mock_task.assert_called_once()
    args, kwargs = mock_task.call_args
    lang_passed = kwargs.get("lang") or (args[4] if len(args) > 4 else None)
    assert lang_passed == "en", f"Expected lang='en', got {lang_passed!r}"

    assert _approval_template("approved", lang_passed) == "approval_approved_en"


# ---------------------------------------------------------------------------
# (c) Unknown language 'xx' → fallback to 'fr' template
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_unknown_lang_falls_back_to_fr_template(db: AsyncSession, approval_setup):
    emp = approval_setup["emp"]
    manager = approval_setup["manager"]
    proj = approval_setup["proj"]

    emp.preferred_language = "xx"
    await db.flush()
    await db.commit()

    week_start = date(2025, 1, 20)
    approval_id = await _submit_week(db, emp, proj, week_start)

    with patch(
        "app.services.approval_service.task_send_approval_notification"
    ) as mock_task:
        svc = ApprovalService(db)
        result = await svc.approve(manager.employee_id, approval_id)

    assert result["status"] == "approved"
    mock_task.assert_called_once()
    args, kwargs = mock_task.call_args
    lang_passed = kwargs.get("lang") or (args[4] if len(args) > 4 else None)
    # lang='xx' is passed through; the template function resolves the fallback
    assert _approval_template("approved", lang_passed) == "approval_approved_fr"


# ---------------------------------------------------------------------------
# (d) Rejection with lang='fr' → rejection French template
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_sends_fr_template(db: AsyncSession, approval_setup):
    emp = approval_setup["emp"]
    manager = approval_setup["manager"]
    proj = approval_setup["proj"]

    emp.preferred_language = "fr"
    await db.flush()
    await db.commit()

    week_start = date(2025, 1, 27)
    approval_id = await _submit_week(db, emp, proj, week_start)

    with patch(
        "app.services.approval_service.task_send_approval_notification"
    ) as mock_task:
        svc = ApprovalService(db)
        result = await svc.reject(
            manager.employee_id, approval_id,
            rejection_reason="Hours are not correct, please review all entries"
        )

    assert result["status"] == "rejected"
    mock_task.assert_called_once()
    args, kwargs = mock_task.call_args
    lang_passed = kwargs.get("lang") or (args[4] if len(args) > 4 else None)
    status_passed = kwargs.get("status") or (args[2] if len(args) > 2 else None)
    assert lang_passed == "fr"
    assert status_passed == "rejected"
    assert _approval_template("rejected", lang_passed) == "approval_rejected_fr"


# ---------------------------------------------------------------------------
# (e) Celery unavailable — main flow is NOT blocked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_resilient_when_task_raises(db: AsyncSession, approval_setup):
    """If the notification task raises, approve() must still succeed."""
    emp = approval_setup["emp"]
    manager = approval_setup["manager"]
    proj = approval_setup["proj"]

    emp.preferred_language = "fr"
    await db.flush()
    await db.commit()

    week_start = date(2025, 2, 3)
    approval_id = await _submit_week(db, emp, proj, week_start)

    with patch(
        "app.services.approval_service.task_send_approval_notification",
        side_effect=Exception("Celery broker unreachable"),
    ):
        svc = ApprovalService(db)
        result = await svc.approve(manager.employee_id, approval_id)

    assert result["status"] == "approved"


@pytest.mark.asyncio
async def test_reject_resilient_when_task_raises(db: AsyncSession, approval_setup):
    """If the notification task raises, reject() must still succeed."""
    emp = approval_setup["emp"]
    manager = approval_setup["manager"]
    proj = approval_setup["proj"]

    emp.preferred_language = "en"
    await db.flush()
    await db.commit()

    week_start = date(2025, 2, 10)
    approval_id = await _submit_week(db, emp, proj, week_start)

    with patch(
        "app.services.approval_service.task_send_approval_notification",
        side_effect=RuntimeError("Redis down"),
    ):
        svc = ApprovalService(db)
        result = await svc.reject(
            manager.employee_id, approval_id,
            rejection_reason="Please review all your entries carefully"
        )

    assert result["status"] == "rejected"
