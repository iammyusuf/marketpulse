from django.contrib import admin

from .models import ScanEvent


@admin.register(ScanEvent)
class ScanEventAdmin(admin.ModelAdmin):
    list_display = ["raw_barcode", "worker", "shop", "product", "scanned_at", "is_duplicate"]
    list_filter = ["shop", "is_duplicate"]
    search_fields = ["raw_barcode"]
