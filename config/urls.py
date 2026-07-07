from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def health_check(request):
    """Проверка живости сервиса — используется для healthcheck'ов и мониторинга."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/accounts/", include("accounts.urls")),
    path("api/organizations/", include("organizations.urls")),
    path("api/scanning/", include("scanning.urls")),
    path("api/integrations/", include("integrations.urls")),
    path("api/payroll/", include("payroll.urls")),
]
