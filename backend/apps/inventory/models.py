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