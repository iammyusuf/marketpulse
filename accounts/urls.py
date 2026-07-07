from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MeView, RegisterView, StaffViewSet

app_name = "accounts"

router = DefaultRouter()
router.register("staff", StaffViewSet, basename="staff")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
] + router.urls
