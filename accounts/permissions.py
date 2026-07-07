from rest_framework import permissions


class IsSameOrganization(permissions.BasePermission):
    """Видеть/редактировать объект может только участник его же организации."""

    def has_object_permission(self, request, view, obj):
        return obj.organization_id == request.user.organization_id


class IsOwner(permissions.BasePermission):
    """Доступ только для пользователей с ролью «владелец»."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)


class IsOwnerOrManager(permissions.BasePermission):
    """Доступ для владельца или менеджера (не для работника)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_owner or user.is_manager))


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Просмотр — всем участникам организации; изменение — только владельцу."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)
