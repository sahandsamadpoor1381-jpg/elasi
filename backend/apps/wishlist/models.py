"""
Customer wishlists.

Each row belongs to exactly one customer, and the unique constraint
makes a product appear at most once per wishlist - so an add can be
idempotent and a double tap can never create duplicates.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)

        constraints = [
            models.UniqueConstraint(
                fields=("user", "product"),
                name="wishlist_unique_user_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.product_id}"
