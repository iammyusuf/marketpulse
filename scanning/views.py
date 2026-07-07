from django.db.models import Case, Count, DecimalField, Sum, Value, When
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role

from .models import ScanEvent
from .serializers import CreateScanEventSerializer, ScanEventSerializer


class ScanEventViewSet(viewsets.ModelViewSet):
    serializer_class = ScanEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = ScanEvent.objects.filter(shop__organization=user.organization)

        if user.role == Role.WORKER:
            qs = qs.filter(worker=user)
        # Владельцы и менеджеры видят все сканирования в рамках своей организации.
        return qs

    def create(self, request, *args, **kwargs):
        serializer = CreateScanEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        scan = ScanEvent.record_scan(
            worker=request.user,
            shop=serializer.validated_data["shop"],
            raw_barcode=serializer.validated_data["raw_barcode"],
        )
        return Response(ScanEventSerializer(scan).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Сводка продуктивности и зарплаты за сегодня по каждому работнику:
        сколько единиц отсканировано (без учёта дубликатов) и сколько заработано.
        """
        today = timezone.now().date()
        qs = self.get_queryset().filter(scanned_at__date=today, is_duplicate=False)

        summary = (
            qs.values("worker_id", "worker__first_name", "worker__last_name")
            .annotate(
                units_scanned=Count("id"),
                earnings=Sum(
                    Case(
                        When(product__isnull=False, then="product__rate_per_unit"),
                        default=Value(0),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    )
                ),
            )
            .order_by("-units_scanned")
        )
        return Response({"date": today, "workers": list(summary)})
