import pytest
from rest_framework.test import APIClient

from accounts.models import CustomUser, Role
from organizations.models import Organization, Shop


@pytest.fixture
def organization():
    return Organization.objects.create(name="Acme LLC")


@pytest.fixture
def shop(organization):
    return Shop.objects.create(organization=organization, name="Main Warehouse")


@pytest.fixture
def owner_user(organization):
    return CustomUser.objects.create_user(
        username="owner1", password="strongpass123", organization=organization, role=Role.OWNER
    )


@pytest.fixture
def manager_user(organization, shop):
    return CustomUser.objects.create_user(
        username="manager1", password="strongpass123", organization=organization, role=Role.MANAGER, shop=shop
    )


@pytest.fixture
def worker_user(organization, shop):
    return CustomUser.objects.create_user(
        username="worker1", password="strongpass123", organization=organization, role=Role.WORKER, shop=shop
    )


@pytest.fixture
def api_client():
    return APIClient()
