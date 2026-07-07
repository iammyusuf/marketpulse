from django.contrib import admin

from .models import Organization, Shop


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "is_active", "created_at"]
    list_filter = ["organization", "is_active"]
