import pytest

from scanning.models import ScanEvent

pytestmark = pytest.mark.django_db


def test_summary_defaults_to_day(api_client, owner_user, shop, worker_user):
    ScanEvent.record_scan(worker=worker_user, shop=shop, raw_barcode="1234567890")
    api_client.force_authenticate(user=owner_user)
    response = api_client.get("/api/scanning/events/summary/")
    assert response.status_code == 200
    assert response.data["period"] == "day"
    assert response.data["workers"][0]["units_scanned"] == 1


def test_summary_accepts_week_and_month(api_client, owner_user, shop, worker_user):
    ScanEvent.record_scan(worker=worker_user, shop=shop, raw_barcode="1234567890")
    api_client.force_authenticate(user=owner_user)

    for period in ("week", "month"):
        response = api_client.get(f"/api/scanning/events/summary/?period={period}")
        assert response.status_code == 200
        assert response.data["period"] == period
        assert response.data["workers"][0]["units_scanned"] == 1


def test_summary_rejects_unknown_period(api_client, owner_user):
    api_client.force_authenticate(user=owner_user)
    response = api_client.get("/api/scanning/events/summary/?period=bogus")
    assert response.status_code == 400


def test_worker_summary_only_shows_own_row(api_client, organization, shop, worker_user):
    other_worker = worker_user.__class__.objects.create_user(
        username="other", password="strongpass123", organization=organization, role=worker_user.role, shop=shop
    )
    ScanEvent.record_scan(worker=worker_user, shop=shop, raw_barcode="1111111111")
    ScanEvent.record_scan(worker=other_worker, shop=shop, raw_barcode="2222222222")

    api_client.force_authenticate(user=worker_user)
    response = api_client.get("/api/scanning/events/summary/")
    assert response.status_code == 200
    assert len(response.data["workers"]) == 1
    assert response.data["workers"][0]["worker_id"] == worker_user.id


def test_manager_summary_scoped_to_own_shop(api_client, organization, shop, manager_user, worker_user):
    from organizations.models import Shop

    other_shop = Shop.objects.create(organization=organization, name="Other Warehouse")
    other_worker = worker_user.__class__.objects.create_user(
        username="other_shop_worker",
        password="strongpass123",
        organization=organization,
        role=worker_user.role,
        shop=other_shop,
    )
    ScanEvent.record_scan(worker=worker_user, shop=shop, raw_barcode="1111111111")
    ScanEvent.record_scan(worker=other_worker, shop=other_shop, raw_barcode="2222222222")

    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/scanning/events/summary/")
    assert response.status_code == 200
    assert len(response.data["workers"]) == 1
    assert response.data["workers"][0]["worker_id"] == worker_user.id
