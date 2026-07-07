import pytest

from accounts.models import CustomUser, Role

pytestmark = pytest.mark.django_db


def test_public_registration_creates_org_and_owner(api_client):
    """Сквозная проверка публичного эндпоинта: создаётся организация и её владелец."""
    response = api_client.post(
        "/api/accounts/register/",
        {"username": "brandnew", "password": "strongpass123", "organization_name": "Fresh Biz"},
    )
    assert response.status_code == 201, response.data
    user = CustomUser.objects.get(username="brandnew")
    assert user.role == Role.OWNER
    assert user.organization.name == "Fresh Biz"
    assert user.organization.owner_id == user.id


def test_owner_can_create_staff(api_client, organization, shop, owner_user):
    """Владелец может создать работника внутри своей организации."""
    api_client.force_authenticate(user=owner_user)
    response = api_client.post(
        "/api/accounts/staff/",
        {
            "username": "newworker",
            "password": "strongpass123",
            "role": Role.WORKER,
            "shop": shop.id,
        },
    )
    assert response.status_code == 201, response.data
    created = CustomUser.objects.get(username="newworker")
    assert created.organization_id == organization.id
    assert created.role == Role.WORKER


def test_manager_cannot_create_staff(api_client, manager_user, shop):
    """Менеджер не может создавать новых сотрудников — это только для владельца."""
    api_client.force_authenticate(user=manager_user)
    response = api_client.post(
        "/api/accounts/staff/",
        {"username": "x", "password": "strongpass123", "role": Role.WORKER, "shop": shop.id},
    )
    assert response.status_code == 403


def test_worker_cannot_create_staff(api_client, worker_user, shop):
    """Работник не может создавать новых сотрудников."""
    api_client.force_authenticate(user=worker_user)
    response = api_client.post(
        "/api/accounts/staff/",
        {"username": "y", "password": "strongpass123", "role": Role.WORKER, "shop": shop.id},
    )
    assert response.status_code == 403


def test_staff_queryset_never_returns_owner_rows(api_client, organization, owner_user, manager_user, worker_user):
    """Список сотрудников никогда не должен включать пользователей с ролью owner."""
    api_client.force_authenticate(user=owner_user)
    response = api_client.get("/api/accounts/staff/")
    assert response.status_code == 200
    usernames = {row["username"] for row in response.data["results"]}
    assert usernames == {manager_user.username, worker_user.username}


def test_organization_is_always_server_set(api_client, owner_user, shop):
    """Клиент не может подменить организацию создаваемого сотрудника."""
    other_org_id = 999999
    api_client.force_authenticate(user=owner_user)
    response = api_client.post(
        "/api/accounts/staff/",
        {
            "username": "smuggler",
            "password": "strongpass123",
            "role": Role.WORKER,
            "shop": shop.id,
            "organization": other_org_id,
        },
    )
    assert response.status_code == 201, response.data
    created = CustomUser.objects.get(username="smuggler")
    assert created.organization_id == owner_user.organization_id


def test_deactivate_staff_soft_deletes(api_client, owner_user, worker_user):
    """DELETE деактивирует пользователя вместо физического удаления."""
    api_client.force_authenticate(user=owner_user)
    response = api_client.delete(f"/api/accounts/staff/{worker_user.id}/")
    assert response.status_code == 204
    worker_user.refresh_from_db()
    assert worker_user.is_active is False
