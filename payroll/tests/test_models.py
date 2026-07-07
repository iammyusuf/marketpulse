from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from payroll.models import PayType, Shift, Tariff

pytestmark = pytest.mark.django_db


def test_current_for_picks_latest_effective_tariff(worker_user):
    """Должен выбираться тариф с самой поздней effective_from, не позднее указанной даты."""
    Tariff.objects.create(
        user=worker_user, pay_type=PayType.PER_UNIT, rate=Decimal("5.00"), effective_from=date(2026, 1, 1)
    )
    newer = Tariff.objects.create(
        user=worker_user, pay_type=PayType.PER_UNIT, rate=Decimal("7.00"), effective_from=date(2026, 6, 1)
    )
    Tariff.objects.create(
        user=worker_user, pay_type=PayType.PER_UNIT, rate=Decimal("9.00"), effective_from=date(2026, 12, 1)
    )

    current = Tariff.current_for(worker_user, pay_type=PayType.PER_UNIT, on_date=date(2026, 7, 1))
    assert current == newer


def test_shift_duration_hours_is_none_while_open(worker_user, shop):
    shift = Shift.objects.create(worker=worker_user, shop=shop, started_at=timezone.now())
    assert shift.duration_hours is None


def test_shift_duration_hours_computed_when_closed(worker_user, shop):
    start = timezone.now()
    shift = Shift.objects.create(
        worker=worker_user, shop=shop, started_at=start, ended_at=start + timedelta(hours=2)
    )
    assert shift.duration_hours == 2.0
