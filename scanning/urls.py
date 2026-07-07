from rest_framework.routers import DefaultRouter

from .views import ScanEventViewSet

app_name = "scanning"

router = DefaultRouter()
router.register("events", ScanEventViewSet, basename="scan-event")

urlpatterns = router.urls
