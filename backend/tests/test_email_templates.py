"""Tests for email template admin routes."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.employee import Employee


def _token(employee_id: int, email: str, role: str) -> str:
    """Helper to create access token for testing."""
    return create_access_token({"sub": email, "employee_id": employee_id, "org_id": 1, "role": role})


async def make_admin(db: AsyncSession, email: str = "admin@test.com") -> Employee:
    """Helper to create an admin user."""
    from datetime import date
    from app.services.auth_service import AuthService
    svc = AuthService(db)
    emp = await svc.create_employee(
        email=email,
        first_name="Admin",
        last_name="User",
        role="admin",
        birth_date=date(1990, 1, 1),
        address="123 Test Street",
    )
    await db.commit()
    return emp


@pytest.mark.asyncio
async def test_list_email_templates(client: AsyncClient, db: AsyncSession):
    """Test GET /api/v1/admin/email-templates returns all templates."""
    admin = await make_admin(db, "admin_templates@test.com")
    
    # List templates
    resp = await client.get(
        "/api/v1/admin/email-templates",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert resp.status_code == 200
    
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least welcome_new_employee and password_reset
    
    # Check structure
    template = data[0]
    assert "key" in template
    assert "subject" in template
    assert "html_body" in template
    assert "is_custom" in template


@pytest.mark.asyncio
async def test_get_email_template(client: AsyncClient, db: AsyncSession):
    """Test GET /api/v1/admin/email-templates/{key} returns specific template."""
    admin = await make_admin(db, "admin_get_template@test.com")
    
    # Get specific template
    resp = await client.get(
        "/api/v1/admin/email-templates/welcome_new_employee",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["key"] == "welcome_new_employee"
    assert data["is_custom"] is False
    assert "{{first_name}}" in data["html_body"] or "{{username}}" in data["html_body"]


@pytest.mark.asyncio
async def test_get_unknown_template_returns_404(client: AsyncClient, db: AsyncSession):
    """Test GET /api/v1/admin/email-templates/{key} with unknown key returns 404."""
    admin = await make_admin(db, "admin_unknown@test.com")
    
    # Get unknown template
    resp = await client.get(
        "/api/v1/admin/email-templates/unknown_template",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_email_template(client: AsyncClient, db: AsyncSession):
    """Test PUT /api/v1/admin/email-templates/{key} updates template."""
    admin = await make_admin(db, "admin_update@test.com")
    
    # Update template
    custom_subject = "Custom Welcome — {{org_name}}"
    custom_body = "<p>Hello {{first_name}}, welcome to {{org_name}}!</p>"
    
    resp = await client.put(
        "/api/v1/admin/email-templates/welcome_new_employee",
        json={
            "subject": custom_subject,
            "html_body": custom_body,
        },
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["key"] == "welcome_new_employee"
    assert data["subject"] == custom_subject
    assert data["html_body"] == custom_body
    assert data["is_custom"] is True
    
    # Verify it persists
    get_resp = await client.get(
        "/api/v1/admin/email-templates/welcome_new_employee",
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["is_custom"] is True
    assert get_data["subject"] == custom_subject


@pytest.mark.asyncio
async def test_update_unknown_template_returns_400(client: AsyncClient, db: AsyncSession):
    """Test PUT /api/v1/admin/email-templates/{key} with unknown key returns 400."""
    admin = await make_admin(db, "admin_update_unknown@test.com")
    
    # Try to update unknown template
    resp = await client.put(
        "/api/v1/admin/email-templates/unknown_template",
        json={
            "subject": "Test",
            "html_body": "<p>Test</p>",
        },
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_send_preview_email(client: AsyncClient, db: AsyncSession):
    """Test POST /api/v1/admin/email-templates/{key}/preview sends preview."""
    admin = await make_admin(db, "admin_preview@test.com")
    
    # Send preview (in dev mode, this just logs)
    resp = await client.post(
        "/api/v1/admin/email-templates/welcome_new_employee/preview",
        json={"to_email": "test@example.com"},
        headers={"Authorization": f"Bearer {_token(admin.employee_id, admin.email, 'admin')}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_employee_cannot_access_email_templates(client: AsyncClient, db: AsyncSession):
    """Test that non-admin users cannot access email template routes."""
    from datetime import date
    from app.services.auth_service import AuthService
    svc = AuthService(db)
    emp = await svc.create_employee(
        email="employee@test.com",
        first_name="Regular",
        last_name="Employee",
        role="employee",
        birth_date=date(1990, 1, 1),
        address="456 Test Avenue",
    )
    await db.commit()
    
    # Try to list templates
    resp = await client.get(
        "/api/v1/admin/email-templates",
        headers={"Authorization": f"Bearer {_token(emp.employee_id, emp.email, 'employee')}"},
    )
    assert resp.status_code == 403
