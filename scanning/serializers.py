from rest_framework import serializers

from organizations.models import Shop

from .models import ScanEvent


class ScanEventSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True, default=None)

    class Meta:
        model = ScanEvent
        fields = [
            "id",
            "worker",
            "shop",
            "product",
            "product_name",
            "raw_barcode",
            "scanned_at",
            "is_duplicate",
        ]
        read_only_fields = ["id", "worker", "product", "scanned_at", "is_duplicate"]


class CreateScanEventSerializer(serializers.Serializer):
    """Сериализатор только для ввода данных в эндпоинт сканирования: склад + штрихкод."""

    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    raw_barcode = serializers.CharField(max_length=64)
