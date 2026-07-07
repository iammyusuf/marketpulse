import pytest
from rest_framework.test import APIRequestFactory

from accounts.models import CustomUser, Role
from accounts.serializers import RegisterSerializer, StaffCreateSerializer
from organizations.models import Organization, Shop

pytestmark = pytest.mark.django_db


def test_register_creates_new_organization_and_forces_owner_role():
    """Публичная регистрация всегда создаёт новую организацию, а роль всегда — владелец."""
    serializer = RegisterSerializer(
        data={
            "username": "newowner",
            "password": "strongpass123",
            "organization_name": "New Biz LLC",
        }
    )
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    assert user.role == Role.OWNER
    assert user.organization is not None
    assert user.organization.name == "New Biz LLC"
    assert user.organization.owner_id == user.id


def test_staff_create_rejects_owner_role(organization, shop, owner_user):
    """StaffCreateSerializer не должен позволять создать пользователя с ролью owner."""
    factory = APIRequestFactory()
    request = factory.post("/api/accounts/staff/")
    request.user = owner_user

    serializer = StaffCreateSerializer(
        data={
            "username": "sneaky",
            "password": "strongpass123",
            "role": Role.OWNER,
            "shop": shop.id,
        },
        context={"request": request},
    )
    assert not serializer.is_valid()
    assert "role" in serializer.errors


def test_staff_create_rejects_shop_from_another_organization(organization, owner_user):
    """Владелец не может назначить работника на склад чужой организации."""
    other_org = Organization.objects.create(name="Other Org")
    other_shop = Shop.objects.create(organization=other_org, name="Other Warehouse")

    factory = APIRequestFactory()
    request = factory.post("/api/accounts/staff/")
    request.user = owner_user

    serializer = StaffCreateSerializer(
        data={
            "username": "worker2",
            "password": "strongpass123",
            "role": Role.WORKER,
            "shop": other_shop.id,
        },
        context={"request": request},
    )
    assert not serializer.is_valid()
    assert "shop" in serializer.errors
