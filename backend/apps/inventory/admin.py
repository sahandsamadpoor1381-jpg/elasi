from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

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
        labels = {
            "variant": "مدل محصول",
            "on_hand": "موجودی فیزیکی (عدد)",
        }
        help_texts = {
            "on_hand": (
                "موجودی فیزیکی کل را وارد کنید، نه مقدار افزایش یا کاهش. "
                "سفارش‌های رزروشده به‌صورت خودکار کم می‌شوند و "
                "هر تغییر در تاریخچه انبار ثبت می‌شود."
            ),
        }

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
    by a stale admin save. On the add path it persists the very
    instance Django Admin supplied (so ``obj.pk`` is populated for
    the log entry and the post-save redirect) with ``reserved=0``,
    and records the opening stock as a single ``adjustment``
    movement in the same transaction.

    A save rejected by the locked re-check is reported through
    ``changeform_view`` as a normal admin error message instead of
    an HTTP 500.
    """

    form = InventoryBalanceAdminForm

    list_select_related = ("variant", "variant__product")

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

    def has_delete_permission(self, request, obj=None) -> bool:
        # Deleting a balance would invalidate stock-ledger reconciliation.
        # Stock must be corrected through the audited adjustment form.
        return False

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

    def changeform_view(
        self,
        request,
        object_id=None,
        form_url="",
        extra_context=None,
    ):
        """Keep a rejected save a normal admin error, never a 500.

        ``save_model`` re-checks ``on_hand >= reserved`` while holding
        ``select_for_update``. If a concurrent reservation commits after
        the form validated, that check raises ``ValidationError`` from
        inside the save path - and Django calls ``save_model`` without
        catching it (options.py:1895), so the exception would otherwise
        surface to the operator as an HTTP 500.

        By the time we get here the admin's own atomic block has already
        rolled the rejected save back, so it is safe to report the error
        and send the operator back to the changelist to retry against
        fresh data.
        """
        try:
            return super().changeform_view(
                request,
                object_id,
                form_url,
                extra_context,
            )
        except ValidationError as exc:
            self.message_user(
                request,
                " ".join(exc.messages),
                messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse(
                    "admin:%s_%s_changelist" % (
                        self.model._meta.app_label,
                        self.model._meta.model_name,
                    ),
                    current_app=self.admin_site.name,
                ),
            )

    @transaction.atomic
    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        if not change:
            # Persist the very instance Django Admin handed us. The
            # normal ModelAdmin lifecycle continues with this object:
            # log_addition() stores object_id=obj.pk (options.py:1901)
            # and response_add() builds the post-save redirect from
            # quote(obj.pk) (options.py:1422). Saving a separate
            # instance leaves obj.pk as None, which writes a log entry
            # with a NULL object_id and redirects to ".../None/change/".
            # reserved stays 0: a brand new balance row has nothing
            # reserved, and the model's reserved<=on_hand check would
            # reject anything else.
            obj.reserved = 0
            obj.save()

            if obj.on_hand:
                StockMovement.objects.create(
                    variant=obj.variant,
                    reason=StockMovement.Reason.ADJUSTMENT,
                    quantity=obj.on_hand,
                    on_hand_delta=obj.on_hand,
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
