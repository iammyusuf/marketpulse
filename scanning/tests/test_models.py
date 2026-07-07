from decimal import Decimal

import pytest

from accounts.models import CustomUser, Role
from integrations.models import Marketplace, MarketplaceConnection, Product
from organizations.models import Organization, Shop
from scanning.models import ScanEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_org():
    org = Organization.objects.create(name="Test Shop LLC")
    shop = Shop.objects.create(organization=org, name="Main Warehouse")
    worker = CustomUser.objects.create_user(
        username="worker1", password="pass12345", organization=org, role=Role.WORKER
    )
    connection = MarketplaceConnection.objects.create(
        organization=org, marketplace=Marketplace.WILDBERRIES, api_key="dummy-key"
    )
    product = Product.objects.create(
        connection=connection,
        barcode="1234567890",
        name="Test T-Shirt",
        rate_per_unit=Decimal("5.00"),
    )
    return {"org": org, "shop": shop, "worker": worker, "product": product}


def test_first_scan_is_not_a_duplicate(setup_org):
    """Первое сканирование штрихкода за день не должно помечаться как дубликат."""
    scan = ScanEvent.record_scan(
        worker=setup_org["worker"], shop=setup_org["shop"], raw_barcode="1234567890"
    )
    assert scan.is_duplicate is False
    assert scan.product == setup_org["product"]


def test_second_same_day_scan_is_flagged_as_duplicate(setup_org):
    """Повторное сканирование того же штрихкода в тот же день помечается как дубликат."""
    ScanEvent.record_scan(
        worker=setup_org["worker"], shop=setup_org["shop"], raw_barcode="1234567890"
    )
    second_scan = ScanEvent.record_scan(
        worker=setup_org["worker"], shop=setup_org["shop"], raw_barcode="1234567890"
    )
    assert second_scan.is_duplicate is True


def test_scan_with_unknown_barcode_has_no_product(setup_org):
    """Штрихкод, которого нет в каталоге, не привязывается ни к какому товару."""
    scan = ScanEvent.record_scan(
        worker=setup_org["worker"], shop=setup_org["shop"], raw_barcode="unknown-barcode"
    )
    assert scan.product is None
    assert scan.is_duplicate is False
