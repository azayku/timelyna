"""Tests for Finance Pro license admin routes."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from app.core.security import create_access_token
from app.models.employee import Employee
from app.services.auth_service import AuthService
from app.utils.module_license import generate_key


def _token(employee_id: int, email: str, role: str) -> str:
    """Helper to create access token for testing."""
    return create_access_token({"sub": email, "employee_id": employee_id, "org_id": 1, "role": role})


async def make_admin(db: AsyncSession, email: str) -> Employee:
    """Helper to create an admin user."""
    svc = AuthService(db)
    admin = await svc.create_employee(
        email=email,
        first_name="Admin",
        last_name="User",
        role="admin",
        birth_date=date(1990, 1, 1),
        address="123 Test Street",
    )
    await db.commit()
    return admin


@pytest.mark.asyncio
async def test_activate_finance_license_success(client: AsyncClient, db: AsyncSession):
    """Test POST /api/v1/admin/finance-license/activate with valid key."""
    admin = await make_admin(db, "admin_finance@test.com")
    
    # Generate a valid license key
    expiry = date.today() + timedelta(days=365)
    license_key = generate_key(expiry)
    
    # Activate license
    resp = await client.post(
        "/api/v1/admin/finance-license/activate",
        json={"license_key": license_key},
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["expiry_date"] == expiry.isoformat()
    assert data["days_remaining"] == 365


@pytest.mark.asyncio
async def test_activate_finance_license_invalid_key(client: AsyncClient, db: AsyncSession):
    """Test POST /api/v1/admin/finance-license/activate with invalid key."""
    admin = await make_admin(db, "admin_finance2@test.com")
    
    # Try to activate with invalid key
    resp = await client.post(
        "/api/v1/admin/finance-license/activate",
        json={"license_key": "INVALID-KEY-12345"},
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    
    assert resp.status_code == 400
    assert "error" in resp.json()["detail"].lower() or "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_finance_license_status_no_license(client: AsyncClient, db: AsyncSession):
    """Test GET /api/v1/admin/finance-license/status when no license is activated."""
    admin = await make_admin(db, "admin_finance3@test.com")
    
    # Clear any existing license from module_licenses
    from sqlalchemy import select, delete
    from app.models.module_license import ModuleLicense
    
    await db.execute(
        delete(ModuleLicense).where(
            ModuleLicense.org_id == 1,
            ModuleLicense.module_name == "finance_pro"
        )
    )
    await db.commit()
    
    # Get status
    resp = await client.get(
        "/api/v1/admin/finance-license/status",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] is False
    assert data["error"] == "No license key activated"


@pytest.mark.asyncio
async def test_get_finance_license_status_active(client: AsyncClient, db: AsyncSession):
    """Test GET /api/v1/admin/finance-license/status with active license."""
    admin = await make_admin(db, "admin_finance4@test.com")
    
    # Generate and activate a valid license key
    expiry = date.today() + timedelta(days=90)
    license_key = generate_key(expiry)
    
    activate_resp = await client.post(
        "/api/v1/admin/finance-license/activate",
        json={"license_key": license_key},
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert activate_resp.status_code == 200
    
    # Get status
    resp = await client.get(
        "/api/v1/admin/finance-license/status",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] is True
    assert data["expiry_date"] == expiry.isoformat()
    assert data["days_remaining"] == 90
    assert data["error"] is None


@pytest.mark.asyncio
async def test_finance_license_requires_admin_role(client: AsyncClient, db: AsyncSession):
    """Test that finance license routes require admin role."""
    # Create a regular employee
    svc = AuthService(db)
    employee = await svc.create_employee(
        email="employee@test.com",
        first_name="Regular",
        last_name="Employee",
        role="employee",
        birth_date=date(1990, 1, 1),
        address="456 Employee Street",
    )
    await db.commit()
    
    # Try to activate license
    resp = await client.post(
        "/api/v1/admin/finance-license/activate",
        json={"license_key": "SOME-KEY"},
        headers={"Authorization": f"Bearer {_token(employee.employee_id, employee.email, 'employee')}"},
    )
    assert resp.status_code == 403
    
    # Try to get status
    resp = await client.get(
        "/api/v1/admin/finance-license/status",
        headers={"Authorization": f"Bearer {_token(employee.employee_id, employee.email, 'employee')}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_activate_license_enables_finance_routes(client: AsyncClient, db: AsyncSession):
    """Test that activating a valid license enables access to finance routes."""
    admin = await make_admin(db, "admin_finance_routes@test.com")
    
    # Generate a valid license key
    expiry = date.today() + timedelta(days=365)
    license_key = generate_key(expiry)
    
    # Activate license
    activate_resp = await client.post(
        "/api/v1/admin/finance-license/activate",
        json={"license_key": license_key},
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert activate_resp.status_code == 200
    
    # Verify finance routes are now accessible
    # Test invoicing route
    invoices_resp = await client.get(
        "/api/v1/finance/invoices",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert invoices_resp.status_code == 200
    
    # Test reporting route
    report_resp = await client.get(
        "/api/v1/admin/organization-statistics?period=this_month",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert report_resp.status_code == 200
    
    # Test finance client report route
    client_report_resp = await client.get(
        "/api/v1/finance/client-report?period=this_month",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert client_report_resp.status_code == 200


@pytest.mark.asyncio
async def test_finance_routes_blocked_without_license(client: AsyncClient, db: AsyncSession):
    """Test that finance routes are blocked when no license is activated."""
    admin = await make_admin(db, "admin_no_license@test.com")
    
    # Clear any existing license
    from sqlalchemy import delete
    from app.models.module_license import ModuleLicense
    
    await db.execute(
        delete(ModuleLicense).where(
            ModuleLicense.org_id == 1,
            ModuleLicense.module_name == "finance_pro"
        )
    )
    await db.commit()
    
    # Try to access finance routes without license
    invoices_resp = await client.get(
        "/api/v1/finance/invoices",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert invoices_resp.status_code == 402
    
    report_resp = await client.get(
        "/api/v1/admin/organization-statistics?period=this_month",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert report_resp.status_code == 402


@pytest.mark.asyncio
async def test_expired_license_returns_402(client: AsyncClient, db: AsyncSession):
    """Test that expired license returns 402 Payment Required on finance routes."""
    admin = await make_admin(db, "admin_expired@test.com")
    
    # Generate an expired license key (expired yesterday)
    expiry = date.today() - timedelta(days=1)
    expired_key = generate_key(expiry)
    
    # Try to activate the expired license
    activate_resp = await client.post(
        "/api/v1/admin/finance-license/activate",
        json={"license_key": expired_key},
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    
    # Activation should fail with 400 because key is expired
    assert activate_resp.status_code == 400
    assert "expired" in activate_resp.json()["detail"].lower()
    
    # Verify finance routes return 402
    invoices_resp = await client.get(
        "/api/v1/finance/invoices",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert invoices_resp.status_code == 402
    
    report_resp = await client.get(
        "/api/v1/finance/client-report?period=this_month",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert report_resp.status_code == 402


@pytest.mark.asyncio
async def test_license_expires_after_activation(client: AsyncClient, db: AsyncSession):
    """Test that a license that expires after activation blocks access."""
    admin = await make_admin(db, "admin_expires_later@test.com")
    
    # Generate a license that expires today (will be valid at activation but expired immediately)
    # We'll manually insert an expired license into the database
    from app.models.module_license import ModuleLicense
    from sqlalchemy import select, delete
    
    # Clear existing licenses
    await db.execute(
        delete(ModuleLicense).where(
            ModuleLicense.org_id == 1,
            ModuleLicense.module_name == "finance_pro"
        )
    )
    await db.commit()
    
    # Insert an expired license directly
    expiry = date.today() - timedelta(days=1)
    expired_license = ModuleLicense(
        org_id=1,
        module_name="finance_pro",
        license_key="EXPIRED-KEY",
        expires_at=expiry,
    )
    db.add(expired_license)
    await db.commit()
    
    # Try to access finance routes - should return 402
    invoices_resp = await client.get(
        "/api/v1/finance/invoices",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert invoices_resp.status_code == 402
    
    # Verify the error message mentions expiration
    error_detail = invoices_resp.json()["detail"]
    assert "expired" in error_detail.lower() or "license" in error_detail.lower()
