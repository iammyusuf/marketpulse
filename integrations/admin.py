from django.contrib import admin

from .models import MarketplaceConnection, Product


@admin.register(MarketplaceConnection)
class MarketplaceConnectionAdmin(admin.ModelAdmin):
    list_display = ["organization", "marketplace", "is_active", "last_synced_at"]
    list_filter = ["marketplace", "is_active"]
    # api_key намеренно не выводится в списке и не используется для поиска/фильтрации.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "barcode", "connection", "rate_per_unit", "updated_at"]
    search_fields = ["name", "barcode"]
