from rest_framework import serializers

from organizations.models import Shop

from .models import Device, ScanEvent


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "shop", "assigned_worker", "identifier", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        request = self.context["request"]
        shop = attrs.get("shop", getattr(self.instance, "shop", None))
        assigned_worker = attrs.get("assigned_worker", getattr(self.instance, "assigned_worker", None))
        if shop and shop.organization_id != request.user.organization_id:
            raise serializers.ValidationError({"shop": "Склад должен принадлежать вашей организации."})
        if assigned_worker and shop and assigned_worker.shop_id != shop.id:
            raise serializers.ValidationError({"assigned_worker": "Работник должен быть закреплён за этим складом."})
        return attrs


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
            "device",
            "is_device_mismatch",
            "unit_rate_snapshot",
            "raw_barcode",
            "scanned_at",
            "is_duplicate",
        ]
        read_only_fields = [
            "id",
            "worker",
            "product",
            "device",
            "is_device_mismatch",
            "unit_rate_snapshot",
            "scanned_at",
            "is_duplicate",
        ]


class CreateScanEventSerializer(serializers.Serializer):
    """Сериализатор только для ввода данных в эндпоинт сканирования: склад + штрихкод + устройство."""

    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    raw_barcode = serializers.CharField(max_length=64)
    device_identifier = serializers.CharField(max_length=64, required=False, allow_blank=True)
