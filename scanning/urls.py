from rest_framework.routers import DefaultRouter

from .views import DeviceViewSet, ScanEventViewSet

app_name = "scanning"

router = DefaultRouter()
router.register("events", ScanEventViewSet, basename="scan-event")
router.register("devices", DeviceViewSet, basename="device")

urlpatterns = router.urls
