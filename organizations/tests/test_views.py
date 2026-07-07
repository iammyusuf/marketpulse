import pytest

from organizations.models import Organization, Shop

pytestmark = pytest.mark.django_db


def test_owner_can_create_shop(api_client, organization, owner_user):
    api_client.force_authenticate(user=owner_user)
    # organization всё равно перезаписывается сервером в perform_create,
    # но сериализатор требует поле в payload'е (см. ShopSerializer).
    response = api_client.post(
        "/api/organizations/shops/", {"name": "Second Warehouse", "organization": organization.id}
    )
    assert response.status_code == 201, response.data


def test_manager_gets_403_on_write(api_client, manager_user, shop):
    api_client.force_authenticate(user=manager_user)
    response = api_client.patch(f"/api/organizations/shops/{shop.id}/", {"name": "Renamed"})
    assert response.status_code == 403


def test_worker_gets_403_on_write(api_client, worker_user, shop):
    api_client.force_authenticate(user=worker_user)
    response = api_client.delete(f"/api/organizations/shops/{shop.id}/")
    assert response.status_code == 403


def test_manager_can_read_shops(api_client, manager_user, shop):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/organizations/shops/")
    assert response.status_code == 200


def test_shop_from_another_organization_is_invisible(api_client, owner_user):
    other_org = Organization.objects.create(name="Other Org")
    other_shop = Shop.objects.create(organization=other_org, name="Other Warehouse")

    api_client.force_authenticate(user=owner_user)
    response = api_client.get(f"/api/organizations/shops/{other_shop.id}/")
    assert response.status_code == 404
