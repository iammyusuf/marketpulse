import pytest

from accounts.models import CustomUser, Role

pytestmark = pytest.mark.django_db


def test_create_user_defaults_to_worker_role():
    """По умолчанию новый пользователь получает роль «работник склада»."""
    user = CustomUser.objects.create_user(username="worker1", password="strongpass123")
    assert user.role == Role.WORKER
    assert user.is_owner is False


def test_owner_role_flags():
    """Флаг is_owner должен быть True только для роли «владелец»."""
    user = CustomUser.objects.create_user(
        username="owner1", password="strongpass123", role=Role.OWNER
    )
    assert user.is_owner is True
    assert user.is_manager is False


def test_user_str_includes_role():
    """Строковое представление пользователя включает его роль."""
    user = CustomUser.objects.create_user(
        username="jane", password="strongpass123", first_name="Jane", role=Role.MANAGER
    )
    assert "manager" in str(user)
