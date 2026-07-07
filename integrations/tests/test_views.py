import pytest

from integrations.models import Marketplace, MarketplaceConnection, Product
from organizations.models import Organization

pytestmark = pytest.mark.django_db


def test_product_list_is_read_only(api_client, organization, owner_user):
    connection = MarketplaceConnection.objects.create(
        organization=organization, marketplace=Marketplace.WILDBERRIES, api_key="fake-key"
    )
    product = Product.objects.create(connection=connection, barcode="1234567890", name="Test Product")

    api_client.force_authenticate(user=owner_user)

    response = api_client.get("/api/integrations/products/")
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == product.id

    response = api_client.post("/api/integrations/products/", {"barcode": "999", "name": "Hack"})
    assert response.status_code == 405


def test_products_are_scoped_to_own_organization(api_client, organization, owner_user):
    other_org = Organization.objects.create(name="Other Org")
    other_connection = MarketplaceConnection.objects.create(
        organization=other_org, marketplace=Marketplace.WILDBERRIES, api_key="fake-key"
    )
    Product.objects.create(connection=other_connection, barcode="0000000000", name="Other Org Product")

    api_client.force_authenticate(user=owner_user)
    response = api_client.get("/api/integrations/products/")
    assert response.status_code == 200
    assert response.data["count"] == 0
