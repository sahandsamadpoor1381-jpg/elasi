from django.contrib import admin

from .models import InventoryBalance, StockMovement


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    """
    Stock intake / correction view.

    ``reserved`` is managed exclusively by the inventory domain
    services (reservation, release, fulfillment) and is read-only
    here: hand-editing it would silently break order reservations.
    ``on_hand`` may be adjusted operationally (stock intake,
    physical count correction); every change is recorded as an
    ``adjustment`` StockMovement so the ledger stays complete.
    """

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
        "reserved",
        "available_stock",
        "updated_at",
    )

    def available_stock(self, obj: InventoryBalance) -> int:
        return obj.available

    available_stock.short_description = "Available"

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        if change:
            previous = (
                InventoryBalance.objects
                .filter(pk=obj.pk)
                .first()
            )

            old_on_hand = (
                previous.on_hand
                if previous is not None
                else 0
            )
        else:
            old_on_hand = 0

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        delta = obj.on_hand - old_on_hand

        if delta != 0:
            StockMovement.objects.create(
                variant=obj.variant,
                reason=StockMovement.Reason.ADJUSTMENT,
                quantity=abs(delta),
                on_hand_delta=delta,
                reserved_delta=0,
            )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """
    Append-only audit view. Movements are written by the inventory
    domain services and can never be created, edited or deleted
    through the admin.
    """

    list_display = (
        "created_at",
        "variant",
        "order",
        "reason",
        "quantity",
        "on_hand_delta",
        "reserved_delta",
    )

    list_filter = (
        "reason",
        "created_at",
    )

    search_fields = (
        "variant__sku",
        "order__public_id",
    )

    readonly_fields = (
        "variant",
        "order",
        "reason",
        "quantity",
        "on_hand_delta",
        "reserved_delta",
        "created_at",
    )

    def has_add_permission(
        self,
        request,
    ) -> bool:
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return False
