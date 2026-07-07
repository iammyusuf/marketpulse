from unittest.mock import MagicMock, patch

import pytest

from integrations.models import Marketplace, MarketplaceConnection, Product
from integrations.tasks import sync_products_for_connection
from organizations.models import Organization

pytestmark = pytest.mark.django_db


FAKE_WB_RESPONSE = {
    "cards": [
        {
            "nmID": "111",
            "title": "Test Hoodie",
            "sizes": [{"skus": ["1111111111"]}],
        }
    ]
}


@patch("integrations.services.wildberries.requests.post")
def test_sync_creates_products_from_wildberries_response(mock_post):
    """После синхронизации товар из ответа Wildberries должен появиться в каталоге."""
    mock_response = MagicMock()
    mock_response.json.return_value = FAKE_WB_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    org = Organization.objects.create(name="Acme LLC")
    connection = MarketplaceConnection.objects.create(
        organization=org, marketplace=Marketplace.WILDBERRIES, api_key="fake-key"
    )

    sync_products_for_connection(connection.id)

    product = Product.objects.get(connection=connection, barcode="1111111111")
    assert product.name == "Test Hoodie"
    connection.refresh_from_db()
    assert connection.last_synced_at is not None


@patch("integrations.services.wildberries.requests.post")
def test_sync_is_idempotent_on_rerun(mock_post):
    """Повторный запуск синхронизации не должен создавать дубликаты товаров."""
    mock_response = MagicMock()
    mock_response.json.return_value = FAKE_WB_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    org = Organization.objects.create(name="Acme LLC")
    connection = MarketplaceConnection.objects.create(
        organization=org, marketplace=Marketplace.WILDBERRIES, api_key="fake-key"
    )

    sync_products_for_connection(connection.id)
    sync_products_for_connection(connection.id)

    assert Product.objects.filter(connection=connection).count() == 1
