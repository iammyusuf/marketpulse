from rest_framework import permissions, viewsets

from .models import Shop
from .serializers import ShopSerializer


class IsSameOrganization(permissions.BasePermission):
    """Видеть/редактировать склад может только участник его же организации."""

    def has_object_permission(self, request, view, obj):
        return obj.organization_id == request.user.organization_id


class ShopViewSet(viewsets.ModelViewSet):
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated, IsSameOrganization]

    def get_queryset(self):
        # Изоляция арендаторов: пользователь видит склады только своей организации.
        return Shop.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
