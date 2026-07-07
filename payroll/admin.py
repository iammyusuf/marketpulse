from django.contrib import admin

from .models import Shift, Tariff


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ["user", "pay_type", "rate", "effective_from"]
    list_filter = ["pay_type"]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ["worker", "shop", "started_at", "ended_at"]
    list_filter = ["shop"]
