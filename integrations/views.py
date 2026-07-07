from rest_framework import permissions, viewsets

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Только чтение: каталог товаров наполняется исключительно Celery-синхронизацией."""

    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Product.objects.filter(connection__organization=self.request.user.organization)
            .select_related("connection")
            .order_by("id")
        )
