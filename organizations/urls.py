from rest_framework.routers import DefaultRouter

from .views import ShopViewSet

app_name = "organizations"

router = DefaultRouter()
router.register("shops", ShopViewSet, basename="shop")

urlpatterns = router.urls
