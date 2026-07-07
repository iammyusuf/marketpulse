from django.contrib import admin

from .models import Device, ScanEvent


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["identifier", "shop", "assigned_worker", "is_active"]
    list_filter = ["shop", "is_active"]


@admin.register(ScanEvent)
class ScanEventAdmin(admin.ModelAdmin):
    list_display = ["raw_barcode", "worker", "shop", "product", "device", "scanned_at", "is_duplicate", "is_device_mismatch"]
    list_filter = ["shop", "is_duplicate", "is_device_mismatch"]
    search_fields = ["raw_barcode"]
