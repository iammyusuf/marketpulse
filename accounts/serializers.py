from rest_framework import serializers

from .models import CustomUser


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
        ]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ["username", "password", "first_name", "last_name", "phone", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        # Пароль обязательно хешируется, а не сохраняется в открытом виде.
        user.set_password(password)
        user.save()
        return user
