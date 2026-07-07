from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "role", "organization", "is_active"]
    list_filter = ["role", "organization", "is_active"]
    fieldsets = UserAdmin.fieldsets + (
        ("Бизнес-данные", {"fields": ("phone", "organization", "role")}),
    )
