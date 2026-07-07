from datetime import date, timedelta
from decimal import Decimal

import pytest

from payroll.models import PayType, Tariff
from scanning.models import Device, ScanEvent

pytestmark = pytest.mark.django_db


def test_owner_can_crud_devices(api_client, owner_user, shop):
    api_client.force_authenticate(user=owner_user)
    response = api_client.post("/api/scanning/devices/", {"shop": shop.id, "identifier": "SCN-001"})
    assert response.status_code == 201, response.data

    device_id = response.data["id"]
    response = api_client.patch(f"/api/scanning/devices/{device_id}/", {"is_active": False})
    assert response.status_code == 200


def test_manager_gets_403_on_device_write(api_client, manager_user, shop):
    api_client.force_authenticate(user=manager_user)
    response = api_client.post("/api/scanning/devices/", {"shop": shop.id, "identifier": "SCN-002"})
    assert response.status_code == 403


def test_manager_can_read_devices(api_client, manager_user, shop):
    Device.objects.create(shop=shop, identifier="SCN-003")
    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/scanning/devices/")
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_worker_gets_403_on_device_list(api_client, worker_user, shop):
    """Устройства — не для работников: ни списка, ни деталей."""
    Device.objects.create(shop=shop, identifier="SCN-004")
    api_client.force_authenticate(user=worker_user)
    response = api_client.get("/api/scanning/devices/")
    assert response.status_code == 403


def test_scan_flags_device_mismatch_but_still_records(shop, worker_user, organization):
    """Скан с чужого устройства помечается флагом, но не блокируется."""
    other_worker = worker_user.__class__.objects.create_user(
        username="other_worker", password="strongpass123", organization=organization, role=worker_user.role, shop=shop
    )
    device = Device.objects.create(shop=shop, identifier="SCN-005", assigned_worker=other_worker)

    scan = ScanEvent.record_scan(
        worker=worker_user, shop=shop, raw_barcode="9999999999", device_identifier="SCN-005"
    )
    assert scan.device_id == device.id
    assert scan.is_device_mismatch is True


def test_unit_rate_snapshot_is_frozen_after_tariff_change(worker_user, shop):
    """Заработок за уже сделанный скан не должен пересчитываться при смене тарифа."""
    Tariff.objects.create(
        user=worker_user, pay_type=PayType.PER_UNIT, rate=Decimal("5.00"), effective_from=date.today() - timedelta(days=1)
    )
    scan = ScanEvent.record_scan(worker=worker_user, shop=shop, raw_barcode="1111111111")
    assert scan.unit_rate_snapshot == Decimal("5.00")

    Tariff.objects.create(user=worker_user, pay_type=PayType.PER_UNIT, rate=Decimal("9.00"), effective_from=date.today())
    scan.refresh_from_db()
    assert scan.unit_rate_snapshot == Decimal("5.00")
