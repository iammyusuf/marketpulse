from rest_framework.routers import DefaultRouter

from .views import ShiftViewSet, TariffViewSet

app_name = "payroll"

router = DefaultRouter()
router.register("shifts", ShiftViewSet, basename="shift")
router.register("tariffs", TariffViewSet, basename="tariff")

urlpatterns = router.urls
