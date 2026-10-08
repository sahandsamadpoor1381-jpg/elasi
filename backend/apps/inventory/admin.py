from django.contrib import admin

from .models import InventoryBalance


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "on_hand",
        "reserved",
        "available_stock",
        "updated_at",
    )

    search_fields = (
        "variant__sku",
        "variant__product__name",
        "variant__product__slug",
    )

    autocomplete_fields = (
        "variant",
    )

    readonly_fields = (
        "available_stock",
        "updated_at",
    )

    def available_stock(self, obj: InventoryBalance) -> int:
        return obj.available

    available_stock.short_description = "Available"