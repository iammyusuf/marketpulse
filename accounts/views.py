from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .mixins import RoleScopedQuerysetMixin
from .models import CustomUser, Role
from .permissions import IsOwner, IsOwnerOrManager
from .serializers import RegisterSerializer, StaffCreateSerializer, StaffSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Публичный эндпоинт для создания новой организации и её владельца."""

    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """Возвращает профиль текущего авторизованного пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class StaffViewSet(RoleScopedQuerysetMixin, viewsets.ModelViewSet):
    """
    Владелец управляет менеджерами/работниками своей организации.
    Менеджер может только просматривать (не редактировать) работников своего
    склада — нужно, например, чтобы выбрать работника при создании смены.
    """

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated(), IsOwnerOrManager()]

    def get_queryset(self):
        # worker сюда не попадает — get_permissions() блокирует его 403-м
        # ещё до вызова queryset (на чтение нужен минимум IsOwnerOrManager).
        qs = CustomUser.objects.filter(role__in=[Role.MANAGER, Role.WORKER]).order_by("username")
        return self.scope_by_role(qs)

    def get_serializer_class(self):
        return StaffCreateSerializer if self.action == "create" else StaffSerializer

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

    def perform_destroy(self, instance):
        # Мягкое удаление: CustomUser связан с ScanEvent/Shift/Tariff,
        # физическое удаление либо упадёт, либо сотрёт историю.
        instance.is_active = False
        instance.save(update_fields=["is_active"])
