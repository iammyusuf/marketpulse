from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    marketplace = serializers.CharField(source="connection.marketplace", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "marketplace", "barcode", "external_id", "name", "rate_per_unit", "updated_at"]
        read_only_fields = fields
