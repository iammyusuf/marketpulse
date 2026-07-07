from django.db import transaction
from rest_framework import serializers

from organizations.models import Organization, Shop

from .models import CustomUser, Role


class UserSerializer(serializers.ModelSerializer):
    """Публичный профиль пользователя — используется в /api/accounts/me/."""

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "organization",
            "shop",
        ]
        read_only_fields = ["id", "role", "organization", "shop"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Публичная регистрация — создаёт НОВУЮ организацию и её владельца.
    Управление менеджерами/работниками внутри уже существующей организации
    выполняется владельцем через StaffCreateSerializer, а не этот эндпоинт.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    organization_name = serializers.CharField(write_only=True, max_length=255)

    class Meta:
        model = CustomUser
        fields = ["username", "password", "first_name", "last_name", "phone", "organization_name"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        organization_name = validated_data.pop("organization_name")

        with transaction.atomic():
            organization = Organization.objects.create(name=organization_name)
            user = CustomUser(organization=organization, role=Role.OWNER, **validated_data)
            # Пароль обязательно хешируется, а не сохраняется в открытом виде.
            user.set_password(password)
            user.save()
            organization.owner = user
            organization.save(update_fields=["owner"])
        return user


class StaffCreateSerializer(serializers.ModelSerializer):
    """Владелец создаёт аккаунт менеджера/работника внутри своей организации."""

    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=[(Role.MANAGER, Role.MANAGER.label), (Role.WORKER, Role.WORKER.label)])
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())

    class Meta:
        model = CustomUser
        fields = ["id", "username", "password", "first_name", "last_name", "phone", "role", "shop"]
        read_only_fields = ["id"]

    def validate_shop(self, shop):
        request = self.context["request"]
        if shop.organization_id != request.user.organization_id:
            raise serializers.ValidationError("Склад должен принадлежать вашей организации.")
        return shop

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StaffSerializer(serializers.ModelSerializer):
    """Просмотр/редактирование существующего менеджера или работника."""

    role = serializers.ChoiceField(choices=[(Role.MANAGER, Role.MANAGER.label), (Role.WORKER, Role.WORKER.label)])
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all(), allow_null=True, required=False)

    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "last_name", "phone", "role", "shop", "is_active"]
        read_only_fields = ["id", "username"]

    def validate_shop(self, shop):
        if shop is None:
            return shop
        request = self.context["request"]
        if shop.organization_id != request.user.organization_id:
            raise serializers.ValidationError("Склад должен принадлежать вашей организации.")
        return shop
