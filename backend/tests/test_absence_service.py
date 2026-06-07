"""
Unit tests for AbsenceService.
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.services.absence_service import AbsenceService
from app.models.absence import Absence
from app.models.employee import Employee


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def absence_service(mock_db):
    """Create an AbsenceService instance with mocked dependencies."""
    return AbsenceService(mock_db)


@pytest.mark.asyncio
async def test_approve_absence_success(absence_service, mock_db):
    """Test successful absence approval."""
    # Mock absence
    absence = Absence(
        id=1,
        employee_id=10,
        absence_type="cp",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 5),
        status="pending",
    )
    
    # Mock employee with correct manager
    employee = Employee(
        employee_id=10,
        email="employee@test.com",
        first_name="John",
        last_name="Doe",
        manager_id=5,
    )
    
    # Setup mocks
    absence_service.repo.get_by_id = AsyncMock(return_value=absence)
    absence_service.emp_repo.get_by_id = AsyncMock(return_value=employee)
    absence_service.repo.update_status = AsyncMock(return_value=absence)
    
    # Call approve with correct manager
    result = await absence_service.approve(manager_id=5, absence_id=1)
    
    # Verify
    assert result["id"] == 1
    absence_service.repo.update_status.assert_called_once()
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_approve_absence_wrong_manager(absence_service):
    """Test that approval fails if manager is not the employee's manager."""
    # Mock absence
    absence = Absence(
        id=1,
        employee_id=10,
        status="pending",
    )
    
    # Mock employee with different manager
    employee = Employee(
        employee_id=10,
        manager_id=5,  # Manager is 5
    )
    
    absence_service.repo.get_by_id = AsyncMock(return_value=absence)
    absence_service.emp_repo.get_by_id = AsyncMock(return_value=employee)
    
    # Try to approve with wrong manager (manager_id=99)
    with pytest.raises(HTTPException) as exc_info:
        await absence_service.approve(manager_id=99, absence_id=1)
    
    assert exc_info.value.status_code == 403
    assert "not the manager" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_approve_already_approved_absence(absence_service):
    """Test that approving an already approved absence fails."""
    # Mock absence that's already approved
    absence = Absence(
        id=1,
        employee_id=10,
        status="approved",  # Already approved
    )
    
    absence_service.repo.get_by_id = AsyncMock(return_value=absence)
    
    # Try to approve again
    with pytest.raises(HTTPException) as exc_info:
        await absence_service.approve(manager_id=5, absence_id=1)
    
    assert exc_info.value.status_code == 400
    assert "cannot approve" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_reject_absence_with_reason(absence_service, mock_db):
    """Test rejecting an absence with a reason."""
    # Mock absence
    absence = Absence(
        id=1,
        employee_id=10,
        status="pending",
    )
    
    # Mock employee
    employee = Employee(
        employee_id=10,
        manager_id=5,
    )
    
    absence_service.repo.get_by_id = AsyncMock(return_value=absence)
    absence_service.emp_repo.get_by_id = AsyncMock(return_value=employee)
    absence_service.repo.update_status = AsyncMock(return_value=absence)
    
    # Reject with reason
    result = await absence_service.reject(
        manager_id=5,
        absence_id=1,
        reason="Insufficient staffing during this period"
    )
    
    # Verify
    assert result["id"] == 1
    absence_service.repo.update_status.assert_called_once()
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_cancel_pending_absence(absence_service, mock_db):
    """Test that employee can cancel their own pending absence."""
    # Mock pending absence
    absence = Absence(
        id=1,
        employee_id=10,
        status="pending",
    )
    
    absence_service.repo.get_by_id = AsyncMock(return_value=absence)
    
    # Cancel as the owner
    await absence_service.cancel(employee_id=10, absence_id=1)
    
    # Verify deletion
    mock_db.delete.assert_called_once_with(absence)
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_cannot_cancel_approved_absence(absence_service):
    """Test that approved absences cannot be cancelled."""
    # Mock approved absence
    absence = Absence(
        id=1,
        employee_id=10,
        status="approved",
    )
    
    absence_service.repo.get_by_id = AsyncMock(return_value=absence)
    
    # Try to cancel
    with pytest.raises(HTTPException) as exc_info:
        await absence_service.cancel(employee_id=10, absence_id=1)
    
    assert exc_info.value.status_code == 400
    assert "pending" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_cannot_cancel_other_employee_absence(absence_service):
    """Test that employee cannot cancel another employee's absence."""
    # Mock absence belonging to employee 10
    absence = Absence(
        id=1,
        employee_id=10,
        status="pending",
    )
    
    absence_service.repo.get_by_id = AsyncMock(return_value=absence)
    
    # Try to cancel as employee 99
    with pytest.raises(HTTPException) as exc_info:
        await absence_service.cancel(employee_id=99, absence_id=1)
    
    assert exc_info.value.status_code == 403
    assert "your own" in str(exc_info.value.detail).lower()
