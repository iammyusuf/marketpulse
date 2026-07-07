from rest_framework import serializers

from accounts.models import Role

from .models import Shift, Tariff


class ShiftSerializer(serializers.ModelSerializer):
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = Shift
        fields = ["id", "worker", "shop", "started_at", "ended_at", "created_by", "note", "duration_hours"]
        read_only_fields = ["id", "created_by", "duration_hours"]

    def validate(self, attrs):
        request = self.context["request"]
        started_at = attrs.get("started_at", getattr(self.instance, "started_at", None))
        ended_at = attrs.get("ended_at", getattr(self.instance, "ended_at", None))
        if ended_at and started_at and ended_at <= started_at:
            raise serializers.ValidationError({"ended_at": "Окончание смены должно быть позже начала."})

        shop = attrs.get("shop", getattr(self.instance, "shop", None))
        worker = attrs.get("worker", getattr(self.instance, "worker", None))
        if shop and shop.organization_id != request.user.organization_id:
            raise serializers.ValidationError({"shop": "Склад должен принадлежать вашей организации."})
        if worker and shop and worker.shop_id != shop.id:
            raise serializers.ValidationError({"worker": "Работник должен быть закреплён за этим складом."})
        if request.user.is_manager and shop and shop.id != request.user.shop_id:
            raise serializers.ValidationError({"shop": "Менеджер может управлять сменами только своего склада."})
        return attrs


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ["id", "user", "pay_type", "rate", "effective_from", "created_by", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate_user(self, user):
        request = self.context["request"]
        if user.organization_id != request.user.organization_id:
            raise serializers.ValidationError("Сотрудник должен принадлежать вашей организации.")
        if user.role == Role.OWNER:
            raise serializers.ValidationError("Нельзя назначить тариф владельцу.")
        return user
