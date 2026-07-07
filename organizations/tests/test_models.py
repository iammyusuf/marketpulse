import pytest

from organizations.models import Organization, Shop

pytestmark = pytest.mark.django_db


def test_shop_str_includes_organization_name():
    org = Organization.objects.create(name="Acme LLC")
    shop = Shop.objects.create(organization=org, name="Main Warehouse")
    assert str(shop) == "Main Warehouse (Acme LLC)"


def test_shops_are_ordered_by_name():
    org = Organization.objects.create(name="Acme LLC")
    Shop.objects.create(organization=org, name="Zeta")
    Shop.objects.create(organization=org, name="Alpha")
    names = list(Shop.objects.values_list("name", flat=True))
    assert names == ["Alpha", "Zeta"]
