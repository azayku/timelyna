"""Unit tests for ReportingService — TEST-REP-001 through TEST-REP-003."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timesheet_entry import TimesheetEntry
from app.services.reporting_service import ReportingService
from app.utils.period import parse_period as _parse_period

from tests.unit.conftest import (
    _make_client,
    _make_employee,
    _make_entry,
    _make_project,
)

PAST_DATE = date(2026, 5, 5)


# ---------------------------------------------------------------------------
# TEST-REP-001 — get_personal_stats calculates billable_pct correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_personal_stats_calculates_billable_pct(db: AsyncSession):
    """Employee has 40h approved: 30h billable + 10h non-billable → 75%."""
    manager = await _make_employee(db, email="rep001mgr@test.com", role="manager")
    emp = await _make_employee(db, email="rep001emp@test.com", manager_id=manager.employee_id)
    client = await _make_client(db, name="RepClient001")
    project = await _make_project(db, client.client_id, manager.employee_id, name="Rep Proj")
    await db.commit()

    # Create approved entries
    # 30h billable across different days in May 2026
    billable_days = [date(2026, 5, 4), date(2026, 5, 5), date(2026, 5, 6)]
    for d in billable_days:
        entry = TimesheetEntry(
            employee_id=emp.employee_id,
            project_id=project.project_id,
            work_date=d,
            hours_worked=Decimal("10.00"),
            description="Billable work",
            task_type="dev",
            entry_type="normal",
            billable_flag=True,
            status="approved",
        )
        db.add(entry)

    # 10h non-billable
    non_billable = TimesheetEntry(
        employee_id=emp.employee_id,
        project_id=project.project_id,
        work_date=date(2026, 5, 7),
        hours_worked=Decimal("10.00"),
        description="Non-billable work",
        task_type="admin",
        entry_type="normal",
        billable_flag=False,
        status="approved",
    )
    db.add(non_billable)
    await db.commit()

    # Mock repository to return controlled data
    mock_repo = MagicMock()
    mock_repo.get_personal_stats = AsyncMock(return_value={
        "total_hours": 40.0,
        "billable_hours": 30.0,
        "days_worked": 4,
        "approved_count": 4,
        "submitted_count": 0,
    })
    mock_repo.get_project_breakdown = AsyncMock(return_value=[])
    mock_repo.get_task_type_breakdown = AsyncMock(return_value=[])
    mock_repo.get_weekly_trend = AsyncMock(return_value=[])

    service = ReportingService(db)
    service.repo = mock_repo

    result = await service.get_personal_stats(
        employee_id=emp.employee_id,
        period="this_month",
    )

    assert result["total_hours"] == 40.0
    assert result["billable_hours"] == 30.0
    assert result["billable_pct"] == 75.0


# ---------------------------------------------------------------------------
# TEST-REP-002 — get_hours_report grouped by employee
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_hours_report_grouped_by_employee(db: AsyncSession):
    """3 employees with entries → get_hours_report returns 3 records."""
    manager = await _make_employee(db, email="rep002mgr@test.com", role="manager")
    client = await _make_client(db, name="RepClient002")
    project = await _make_project(db, client.client_id, manager.employee_id, name="Team Proj")
    await db.commit()

    employees = []
    for i in range(3):
        emp = await _make_employee(db, email=f"rep002emp{i}@test.com", manager_id=manager.employee_id)
        employees.append(emp)
        # Use different dates per employee to avoid unique constraint
        work_day = date(2026, 5, 4 + i)
        await _make_entry(db, emp.employee_id, project.project_id, work_day, hours=8.0, status="approved")
    await db.commit()

    # Mock the repository response
    mock_repo = MagicMock()
    mock_repo.get_hours_report = AsyncMock(return_value=[
        {
            "employee_id": employees[0].employee_id,
            "employee_name": "Rep Emp 0",
            "total_hours": 8.0,
            "billable_hours": 8.0,
            "non_billable_hours": 0.0,
        },
        {
            "employee_id": employees[1].employee_id,
            "employee_name": "Rep Emp 1",
            "total_hours": 8.0,
            "billable_hours": 8.0,
            "non_billable_hours": 0.0,
        },
        {
            "employee_id": employees[2].employee_id,
            "employee_name": "Rep Emp 2",
            "total_hours": 8.0,
            "billable_hours": 8.0,
            "non_billable_hours": 0.0,
        },
    ])

    service = ReportingService(db)
    service.repo = mock_repo

    result = await service.get_hours_report(
        date_from=date(2026, 5, 1),
        date_to=date(2026, 5, 31),
        group_by="employee",
    )

    assert len(result) == 3
    employee_ids_in_result = [r["employee_id"] for r in result]
    for emp in employees:
        assert emp.employee_id in employee_ids_in_result


# ---------------------------------------------------------------------------
# TEST-REP-003 — _parse_period("this_month") returns correct dates for May 2026
# ---------------------------------------------------------------------------

def test_parse_period_this_month_returns_correct_dates():
    """Call _parse_period('this_month') in May 2026 context.

    Since the test environment's current date is 2026-05-06,
    we patch date.today() to ensure consistent results regardless of when tests run.
    """
    from unittest.mock import patch
    from datetime import date as _date

    with patch("app.utils.period.date") as mock_date:
        mock_date.today.return_value = _date(2026, 5, 6)
        mock_date.side_effect = lambda *args, **kwargs: _date(*args, **kwargs)

        start, end = _parse_period("this_month")

    assert start == _date(2026, 5, 1)
    assert end == _date(2026, 5, 6)  # end = today
