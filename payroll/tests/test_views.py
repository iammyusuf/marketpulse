from datetime import date
from decimal import Decimal

import pytest

from organizations.models import Shop
from payroll.models import PayType, Shift, Tariff

pytestmark = pytest.mark.django_db


def test_worker_clock_in_and_clock_out(api_client, worker_user, shop):
    api_client.force_authenticate(user=worker_user)

    response = api_client.post("/api/payroll/shifts/clock_in/", {"shop": shop.id})
    assert response.status_code == 201, response.data
    assert response.data["ended_at"] is None

    response = api_client.post("/api/payroll/shifts/clock_out/")
    assert response.status_code == 200, response.data
    assert response.data["ended_at"] is not None


def test_worker_cannot_clock_in_twice(api_client, worker_user, shop):
    api_client.force_authenticate(user=worker_user)
    api_client.post("/api/payroll/shifts/clock_in/", {"shop": shop.id})
    response = api_client.post("/api/payroll/shifts/clock_in/", {"shop": shop.id})
    assert response.status_code == 400


def test_manager_can_create_shift_for_own_shop_worker(api_client, manager_user, worker_user, shop):
    api_client.force_authenticate(user=manager_user)
    response = api_client.post(
        "/api/payroll/shifts/",
        {"worker": worker_user.id, "shop": shop.id, "started_at": "2026-07-01T09:00:00Z"},
    )
    assert response.status_code == 201, response.data


def test_manager_cannot_create_shift_for_other_shop(api_client, organization, manager_user, shop):
    other_shop = Shop.objects.create(organization=organization, name="Other Warehouse")
    other_worker = manager_user.__class__.objects.create_user(
        username="other_worker", password="strongpass123", organization=organization, role="worker", shop=other_shop
    )
    api_client.force_authenticate(user=manager_user)
    response = api_client.post(
        "/api/payroll/shifts/",
        {"worker": other_worker.id, "shop": other_shop.id, "started_at": "2026-07-01T09:00:00Z"},
    )
    assert response.status_code == 400


def test_worker_cannot_write_shifts(api_client, worker_user, shop):
    api_client.force_authenticate(user=worker_user)
    response = api_client.post(
        "/api/payroll/shifts/",
        {"worker": worker_user.id, "shop": shop.id, "started_at": "2026-07-01T09:00:00Z"},
    )
    assert response.status_code == 403


def test_worker_can_read_own_shifts(api_client, worker_user, shop):
    Shift.objects.create(worker=worker_user, shop=shop, started_at="2026-07-01T09:00:00Z", created_by=worker_user)
    api_client.force_authenticate(user=worker_user)
    response = api_client.get("/api/payroll/shifts/")
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_owner_only_can_crud_tariffs(api_client, owner_user, manager_user, worker_user):
    api_client.force_authenticate(user=owner_user)
    response = api_client.post(
        "/api/payroll/tariffs/",
        {"user": worker_user.id, "pay_type": PayType.PER_UNIT, "rate": "5.00", "effective_from": date.today()},
    )
    assert response.status_code == 201, response.data

    api_client.force_authenticate(user=manager_user)
    response = api_client.post(
        "/api/payroll/tariffs/",
        {"user": worker_user.id, "pay_type": PayType.PER_UNIT, "rate": "5.00", "effective_from": date.today()},
    )
    assert response.status_code == 403


def test_tariff_cannot_target_owner(api_client, owner_user):
    api_client.force_authenticate(user=owner_user)
    response = api_client.post(
        "/api/payroll/tariffs/",
        {"user": owner_user.id, "pay_type": PayType.PER_UNIT, "rate": "5.00", "effective_from": date.today()},
    )
    assert response.status_code == 400
