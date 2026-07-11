"""
Unit tests for timesheet reminder tasks.
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from app.tasks.reminder_tasks import _get_employees_with_missing_timesheets


_UNSET = object()


def _make_execute_result(scalars_all=None, scalar_one_or_none=_UNSET):
    """Create a mock execute result that works synchronously."""
    result = MagicMock()
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    if scalar_one_or_none is not _UNSET:
        result.scalar_one_or_none.return_value = scalar_one_or_none
    return result


def _make_db(*execute_returns):
    """Create a mock DB that returns given values for successive execute() calls."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = list(execute_returns)
    return mock_db


@pytest.mark.asyncio
async def test_reminder_with_entries_no_reminder():
    """Employees with entries don't get reminders."""
    employee = MagicMock()
    employee.employee_id = 1

    db = _make_db(
        _make_execute_result(scalars_all=[employee]),   # active employees
        _make_execute_result(scalars_all=[MagicMock()]),  # has entries
        _make_execute_result(scalar_one_or_none=None),  # no full absence
    )

    result = await _get_employees_with_missing_timesheets(db, date(2024, 1, 1), date(2024, 1, 7))
    assert len(result) == 0


@pytest.mark.asyncio
async def test_reminder_without_entries_sends_reminder():
    """Employees without entries get reminders."""
    employee = MagicMock()
    employee.employee_id = 1

    db = _make_db(
        _make_execute_result(scalars_all=[employee]),   # active employees
        _make_execute_result(scalars_all=[]),           # no entries
        _make_execute_result(scalar_one_or_none=None),  # no full absence
        _make_execute_result(scalar_one_or_none=None),  # no pref → default enabled
    )

    result = await _get_employees_with_missing_timesheets(db, date(2024, 1, 1), date(2024, 1, 7))
    assert len(result) == 1
    assert result[0].employee_id == 1


@pytest.mark.asyncio
async def test_reminder_absent_entire_week_no_reminder():
    """Employees absent for entire period don't get reminders."""
    employee = MagicMock()
    employee.employee_id = 1

    absence = MagicMock()
    absence.start_date = date(2023, 12, 25)
    absence.end_date = date(2024, 1, 10)
    absence.status = "approved"

    db = _make_db(
        _make_execute_result(scalars_all=[employee]),   # active employees
        _make_execute_result(scalars_all=[]),           # no entries
        _make_execute_result(scalar_one_or_none=absence),  # full period absence
    )

    result = await _get_employees_with_missing_timesheets(db, date(2024, 1, 1), date(2024, 1, 7))
    assert len(result) == 0


@pytest.mark.asyncio
async def test_reminder_preferences_disabled_no_reminder():
    """Employees with email disabled don't get reminders."""
    employee = MagicMock()
    employee.employee_id = 1

    pref = MagicMock()
    pref.email_enabled = False

    db = _make_db(
        _make_execute_result(scalars_all=[employee]),   # active employees
        _make_execute_result(scalars_all=[]),           # no entries
        _make_execute_result(scalar_one_or_none=None),  # no full absence
        _make_execute_result(scalar_one_or_none=pref),  # pref disabled
    )

    result = await _get_employees_with_missing_timesheets(db, date(2024, 1, 1), date(2024, 1, 7))
    assert len(result) == 0


@pytest.mark.asyncio
async def test_inactive_employee_no_reminder():
    """Inactive employees are excluded from the query."""
    db = _make_db(
        _make_execute_result(scalars_all=[]),  # no active employees returned
    )

    result = await _get_employees_with_missing_timesheets(db, date(2024, 1, 1), date(2024, 1, 7))
    assert len(result) == 0
