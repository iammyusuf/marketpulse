from rest_framework import permissions, viewsets

from accounts.permissions import IsOwnerOrReadOnly, IsSameOrganization

from .models import Shop
from .serializers import ShopSerializer


class ShopViewSet(viewsets.ModelViewSet):
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly, IsSameOrganization]

    def get_queryset(self):
        # Изоляция арендаторов: пользователь видит склады только своей организации.
        return Shop.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
