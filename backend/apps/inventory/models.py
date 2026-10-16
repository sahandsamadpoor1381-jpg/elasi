from django.db import models
from django.db.models import F, Q

from apps.catalog.models import ProductVariant


class InventoryBalance(models.Model):
    variant = models.OneToOneField(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory",
    )

    on_hand = models.PositiveIntegerField(
        default=0,
    )

    reserved = models.PositiveIntegerField(
        default=0,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(reserved__lte=F("on_hand")),
                name="inventory_reserved_lte_on_hand",
            ),
        ]

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved

    def __str__(self) -> str:
        return f"{self.variant.sku} inventory"


class StockMovement(models.Model):
    """
    Append-only audit ledger for every change to inventory
    counters.

    Rows are created only by the inventory domain services
    (reservation, release, fulfillment) and by audited admin
    stock adjustments. They are never edited or deleted through
    the admin.

    ``on_hand_delta`` / ``reserved_delta`` mirror the exact
    change applied to the related ``InventoryBalance`` row so
    the ledger can be reconciled against the balances.
    """

    class Reason(models.TextChoices):
        RESERVATION = (
            "reservation",
            "Reservation",
        )

        RELEASE = (
            "release",
            "Release",
        )

        FULFILLMENT = (
            "fulfillment",
            "Fulfillment",
        )

        ADJUSTMENT = (
            "adjustment",
            "Adjustment",
        )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )

    reason = models.CharField(
        max_length=20,
        choices=Reason.choices,
    )

    quantity = models.PositiveIntegerField()

    on_hand_delta = models.IntegerField()

    reserved_delta = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = (
            "-created_at",
            "-pk",
        )

        indexes = [
            models.Index(
                fields=(
                    "variant",
                    "created_at",
                ),
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.get_reason_display()} "
            f"{self.variant.sku} x{self.quantity}"
        )