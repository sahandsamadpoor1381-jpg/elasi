from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import InventoryBalance, StockMovement


class InventoryBalanceAdminForm(forms.ModelForm):
    """Form-level validation for the common, non-raced case.

    The authoritative check runs again under a row lock in
    ``InventoryBalanceAdmin.save_model`` (see there); this form
    gives the admin a friendly inline error for the usual case.
    """

    class Meta:
        model = InventoryBalance
        fields = (
            "variant",
            "on_hand",
        )

    def clean_on_hand(self):
        on_hand = self.cleaned_data["on_hand"]

        if self.instance.pk:
            current = (
                InventoryBalance.objects
                .filter(pk=self.instance.pk)
                .values("reserved")
                .first()
            )

            if (
                current is not None
                and on_hand < current["reserved"]
            ):
                raise ValidationError(
                    "on_hand cannot be lower than the "
                    "currently reserved quantity (%d). "
                    "Fulfill or release the reserved "
                    "orders first." % current["reserved"],
                )

        return on_hand


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

    ``save_model`` applies adjustments atomically under a row lock:
    it re-reads the latest ``reserved``/``on_hand`` inside the
    transaction instead of trusting the (possibly stale) form
    instance, so a concurrent reservation can never be clobbered
    by a stale admin save.
    """

    form = InventoryBalanceAdminForm

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

    def get_readonly_fields(self, request, obj=None):
        # A balance row's variant is its identity; re-pointing it
        # after creation would orphan the ledger, so it becomes
        # read-only on the change form.
        if obj is not None and obj.pk:
            return self.readonly_fields + ("variant",)
        return self.readonly_fields

    @transaction.atomic
    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        if not change:
            balance = InventoryBalance(
                variant=obj.variant,
                on_hand=obj.on_hand,
                reserved=0,
            )
            balance.save()

            if balance.on_hand:
                StockMovement.objects.create(
                    variant=balance.variant,
                    reason=StockMovement.Reason.ADJUSTMENT,
                    quantity=balance.on_hand,
                    on_hand_delta=balance.on_hand,
                    reserved_delta=0,
                )
            return

        locked = (
            InventoryBalance.objects
            .select_for_update()
            .get(pk=obj.pk)
        )

        old_on_hand = locked.on_hand
        new_on_hand = obj.on_hand

        if new_on_hand < locked.reserved:
            raise ValidationError(
                {
                    "on_hand": (
                        "on_hand cannot be lower than the "
                        "currently reserved quantity (%d). "
                        "Fulfill or release the reserved "
                        "orders first." % locked.reserved
                    ),
                },
            )

        delta = new_on_hand - old_on_hand

        if delta == 0:
            return

        locked.on_hand = new_on_hand

        locked.save(
            update_fields=(
                "on_hand",
                "updated_at",
            ),
        )

        StockMovement.objects.create(
            variant=locked.variant,
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
