from decimal import Decimal

from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.mixins import RoleScopedQuerysetMixin
from accounts.permissions import IsOwner, IsOwnerOrManager
from payroll.models import PayType, Tariff

from .models import Device, ScanEvent
from .serializers import CreateScanEventSerializer, DeviceSerializer, ScanEventSerializer
from .utils import resolve_period


def _latest_tariffs_by_user(user_ids, as_of_date):
    rows = Tariff.objects.filter(user_id__in=user_ids, effective_from__lte=as_of_date).order_by(
        "user_id", "-effective_from", "-id"
    )
    latest = {}
    for tariff in rows:
        latest.setdefault(tariff.user_id, tariff)
    return latest


def _hours_worked_by_user(user_ids, start, end):
    # Считается в Python, а не через агрегацию по разнице дат в БД: SQLite (dev/test)
    # и Postgres (prod) по-разному работают с арифметикой над DateTimeField.
    from payroll.models import Shift

    shifts = Shift.objects.filter(
        worker_id__in=user_ids,
        started_at__date__gte=start,
        started_at__date__lte=end,
        ended_at__isnull=False,
    )
    hours = {}
    for shift in shifts:
        duration = Decimal(str((shift.ended_at - shift.started_at).total_seconds() / 3600))
        hours[shift.worker_id] = hours.get(shift.worker_id, Decimal("0")) + duration
    return hours


class DeviceViewSet(RoleScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    org_lookup = "shop__organization"
    shop_lookup = "shop"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), IsOwnerOrManager()]
        return [permissions.IsAuthenticated(), IsOwner()]

    def get_queryset(self):
        # worker сюда никогда не попадает — get_permissions() блокирует
        # его 403-м ещё до вызова queryset (IsOwnerOrManager на чтение).
        qs = Device.objects.select_related("shop", "assigned_worker")
        return self.scope_by_role(qs)


class ScanEventViewSet(RoleScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ScanEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    org_lookup = "shop__organization"
    shop_lookup = "shop"
    worker_lookup = "worker"

    def get_queryset(self):
        return self.scope_by_role(ScanEvent.objects.all())

    def create(self, request, *args, **kwargs):
        serializer = CreateScanEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        scan = ScanEvent.record_scan(
            worker=request.user,
            shop=serializer.validated_data["shop"],
            raw_barcode=serializer.validated_data["raw_barcode"],
            device_identifier=serializer.validated_data.get("device_identifier") or None,
        )
        return Response(ScanEventSerializer(scan).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Сводка продуктивности и зарплаты по каждому работнику за период
        (день/неделя/месяц): сколько единиц отсканировано (без учёта
        дубликатов) и сколько заработано.
        """
        period = request.query_params.get("period", "day")
        try:
            start, end = resolve_period(period)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(scanned_at__date__range=(start, end), is_duplicate=False)

        scan_rows = list(
            qs.values("worker_id", "worker__first_name", "worker__last_name")
            .annotate(
                units_scanned=Count("id"),
                unit_earnings=Sum(
                    Coalesce(
                        "unit_rate_snapshot", Value(0), output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
            )
            .order_by("-units_scanned")
        )

        worker_ids = [row["worker_id"] for row in scan_rows]
        tariffs = _latest_tariffs_by_user(worker_ids, as_of_date=end)
        hours_by_worker = _hours_worked_by_user(worker_ids, start, end)

        workers = []
        for row in scan_rows:
            tariff = tariffs.get(row["worker_id"])
            earnings = row["unit_earnings"]
            if tariff and tariff.pay_type == PayType.HOURLY:
                earnings = hours_by_worker.get(row["worker_id"], Decimal("0")) * tariff.rate
            elif tariff and tariff.pay_type == PayType.FIXED_MONTHLY:
                # Пропорциональный расчёт для day/week не определён бизнес-правилами —
                # намеренно оставлено None, а не угадано, до отдельного уточнения.
                earnings = tariff.rate if period == "month" else None
            workers.append({**row, "earnings": earnings})

        return Response({"period": period, "start": start, "end": end, "workers": workers})
