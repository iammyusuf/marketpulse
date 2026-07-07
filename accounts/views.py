from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser, Role
from .permissions import IsOwner
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


class StaffViewSet(viewsets.ModelViewSet):
    """Владелец управляет менеджерами/работниками своей организации."""

    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return CustomUser.objects.filter(
            organization=self.request.user.organization,
            role__in=[Role.MANAGER, Role.WORKER],
        ).order_by("username")

    def get_serializer_class(self):
        return StaffCreateSerializer if self.action == "create" else StaffSerializer

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

    def perform_destroy(self, instance):
        # Мягкое удаление: CustomUser связан с ScanEvent/Shift/Tariff,
        # физическое удаление либо упадёт, либо сотрёт историю.
        instance.is_active = False
        instance.save(update_fields=["is_active"])
