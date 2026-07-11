"""Tests unitaires pour les entry templates."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.entry_template import EntryTemplate
from app.models.project import Project


async def _auth_headers(client: AsyncClient, identifier: str, password: str) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_entry_template(
    client: AsyncClient,
    db: AsyncSession,
    regular_employee: Employee,
) -> None:
    """Test de création d'un template d'entrée."""
    headers = await _auth_headers(client, "employee@test.com", "SecurePass123")

    # Données du template
    template_data = {
        "name": "Dev Backend Sprint",
        "project_id": 1,
        "task_type": "development",
        "description": "Développement backend",
        "default_hours": 8.0,
        "is_favorite": True,
    }

    # Appel API
    response = await client.post(
        "/api/v1/entry-templates/",
        json=template_data,
        headers=headers,
    )

    # Vérifications
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == template_data["name"]
    assert data["task_type"] == template_data["task_type"]
    assert data["default_hours"] == template_data["default_hours"]
    assert data["is_favorite"] is True
    assert "template_id" in data
    assert data["employee_id"] == regular_employee.employee_id


@pytest.mark.asyncio
async def test_get_my_templates(
    client: AsyncClient,
    db: AsyncSession,
    regular_employee: Employee,
) -> None:
    """Test de récupération des templates de l'employé."""
    headers = await _auth_headers(client, "employee@test.com", "SecurePass123")

    # Créer quelques templates
    templates = [
        EntryTemplate(
            employee_id=regular_employee.employee_id,
            org_id=1,
            name="Template 1",
            task_type="development",
            is_favorite=True,
        ),
        EntryTemplate(
            employee_id=regular_employee.employee_id,
            org_id=1,
            name="Template 2",
            task_type="testing",
            is_favorite=False,
        ),
    ]
    for tpl in templates:
        db.add(tpl)
    await db.commit()

    # Appel API
    response = await client.get("/api/v1/entry-templates/", headers=headers)

    # Vérifications
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Les favoris doivent être en premier
    assert data[0]["is_favorite"] is True


@pytest.mark.asyncio
async def test_update_entry_template(
    client: AsyncClient,
    db: AsyncSession,
    regular_employee: Employee,
) -> None:
    """Test de mise à jour d'un template."""
    headers = await _auth_headers(client, "employee@test.com", "SecurePass123")

    # Créer un template
    template = EntryTemplate(
        employee_id=regular_employee.employee_id,
        org_id=1,
        name="Original Name",
        is_favorite=False,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    # Mettre à jour
    update_data = {
        "name": "Updated Name",
        "is_favorite": True,
    }
    response = await client.put(
        f"/api/v1/entry-templates/{template.template_id}",
        json=update_data,
        headers=headers,
    )

    # Vérifications
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_favorite"] is True


@pytest.mark.asyncio
async def test_delete_entry_template(
    client: AsyncClient,
    db: AsyncSession,
    regular_employee: Employee,
) -> None:
    """Test de suppression d'un template."""
    headers = await _auth_headers(client, "employee@test.com", "SecurePass123")

    # Créer un template
    template = EntryTemplate(
        employee_id=regular_employee.employee_id,
        org_id=1,
        name="To Delete",
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    # Supprimer
    response = await client.delete(
        f"/api/v1/entry-templates/{template.template_id}",
        headers=headers,
    )

    # Vérifications
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # Vérifier que le template n'existe plus
    get_response = await client.get(
        f"/api/v1/entry-templates/{template.template_id}",
        headers=headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_template_limit(
    client: AsyncClient,
    db: AsyncSession,
    regular_employee: Employee,
) -> None:
    """Test de la limite de 20 templates par employé."""
    headers = await _auth_headers(client, "employee@test.com", "SecurePass123")

    # Créer 20 templates
    for i in range(20):
        template = EntryTemplate(
            employee_id=regular_employee.employee_id,
            org_id=1,
            name=f"Template {i}",
        )
        db.add(template)
    await db.commit()

    # Essayer d'en créer un 21ème
    response = await client.post(
        "/api/v1/entry-templates/",
        json={"name": "Template 21"},
        headers=headers,
    )

    # Doit échouer
    assert response.status_code == 400
    assert "20 templates" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_template_isolation_multi_tenant(
    client: AsyncClient,
    db: AsyncSession,
    regular_employee: Employee,
) -> None:
    """Test de l'isolation multi-tenant : un employé ne peut pas voir les templates d'un autre."""
    headers = await _auth_headers(client, "employee@test.com", "SecurePass123")

    # Créer un template pour un autre employé (ID 9999)
    other_template = EntryTemplate(
        employee_id=9999,
        org_id=1,
        name="Other Employee Template",
    )
    db.add(other_template)
    await db.commit()
    await db.refresh(other_template)

    # L'employé courant ne doit pas pouvoir y accéder
    response = await client.get(
        f"/api/v1/entry-templates/{other_template.template_id}",
        headers=headers,
    )
    assert response.status_code == 404

    # L'employé courant ne doit pas le voir dans sa liste
    list_response = await client.get("/api/v1/entry-templates/", headers=headers)
    data = list_response.json()
    template_ids = [t["template_id"] for t in data]
    assert other_template.template_id not in template_ids
