from rest_framework import serializers

from .models import Organization, Shop


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "owner", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "organization", "name", "description", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
