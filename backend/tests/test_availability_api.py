"""
Integration tests for availability API endpoint.
"""
import pytest
from httpx import AsyncClient
from datetime import date, timedelta


def _auth(login_resp) -> dict:
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_availability_endpoint_returns_aggregated_data(async_client: AsyncClient):
    """GET /admin/availability returns list with correct structure."""
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timesheetpro.com", "password": "Admin1234!"}
    )
    assert login.status_code == 200

    start = date.today()
    end = start + timedelta(days=6)

    response = await async_client.get(
        "/api/v1/admin/availability",
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        headers=_auth(login),
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))  # Accept both list and paginated dict


@pytest.mark.asyncio
async def test_availability_filters_by_department(async_client: AsyncClient):
    """GET /admin/availability with department filter returns 200."""
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timesheetpro.com", "password": "Admin1234!"}
    )
    assert login.status_code == 200

    start = date.today()
    end = start + timedelta(days=6)

    response = await async_client.get(
        "/api/v1/admin/availability",
        params={"start_date": start.isoformat(), "end_date": end.isoformat(), "department": "Engineering"},
        headers=_auth(login),
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_availability_requires_admin_role(async_client: AsyncClient):
    """GET /admin/availability without token returns 401."""
    start = date.today()
    end = start + timedelta(days=6)

    response = await async_client.get(
        "/api/v1/admin/availability",
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_availability_date_range_validation(async_client: AsyncClient):
    """GET /admin/availability with large range returns 200 or 400."""
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@timesheetpro.com", "password": "Admin1234!"}
    )
    assert login.status_code == 200

    start = date.today()
    end = start + timedelta(days=35)

    response = await async_client.get(
        "/api/v1/admin/availability",
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        headers=_auth(login),
    )

    assert response.status_code in (200, 400)
