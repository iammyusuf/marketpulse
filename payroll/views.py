from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.mixins import RoleScopedQuerysetMixin
from accounts.permissions import IsOwner, IsOwnerOrManager
from organizations.models import Shop

from .models import Shift, Tariff
from .serializers import ShiftSerializer, TariffSerializer


class ShiftViewSet(RoleScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    org_lookup = "shop__organization"
    shop_lookup = "shop"
    worker_lookup = "worker"

    def get_queryset(self):
        return self.scope_by_role(Shift.objects.select_related("worker", "shop"))

    def get_permissions(self):
        if self.action in ("clock_in", "clock_out", "list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrManager()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["post"])
    def clock_in(self, request):
        shop = get_object_or_404(Shop, pk=request.data.get("shop"), organization=request.user.organization)
        if Shift.objects.filter(worker=request.user, ended_at__isnull=True).exists():
            return Response({"detail": "У вас уже есть открытая смена."}, status=status.HTTP_400_BAD_REQUEST)
        shift = Shift.objects.create(
            worker=request.user, shop=shop, started_at=timezone.now(), created_by=request.user
        )
        return Response(ShiftSerializer(shift).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def clock_out(self, request):
        shift = Shift.objects.filter(worker=request.user, ended_at__isnull=True).order_by("-started_at").first()
        if not shift:
            return Response({"detail": "Нет открытой смены."}, status=status.HTTP_400_BAD_REQUEST)
        shift.ended_at = timezone.now()
        shift.save(update_fields=["ended_at"])
        return Response(ShiftSerializer(shift).data)


class TariffViewSet(viewsets.ModelViewSet):
    """Тарифы — только владелец: самая чувствительная финансовая поверхность API."""

    serializer_class = TariffSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Tariff.objects.filter(user__organization=self.request.user.organization).select_related("user")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
