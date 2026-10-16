import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.catalog.models import ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = (
            "pending_payment",
            "Pending payment",
        )
        PAID = (
            "paid",
            "Paid",
        )
        PROCESSING = (
            "processing",
            "Processing",
        )
        SHIPPED = (
            "shipped",
            "Shipped",
        )
        DELIVERED = (
            "delivered",
            "Delivered",
        )
        CANCELLED = (
            "cancelled",
            "Cancelled",
        )
        EXPIRED = (
            "expired",
            "Expired",
        )

    class ShippingMethod(models.TextChoices):
        POSTAL = (
            "postal",
            "Postal",
        )

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
    )

    shipping_method = models.CharField(
        max_length=20,
        choices=ShippingMethod.choices,
        default=ShippingMethod.POSTAL,
    )

    subtotal_rial = models.PositiveBigIntegerField()

    shipping_fee_rial = models.PositiveBigIntegerField(
        default=0,
    )

    total_rial = models.PositiveBigIntegerField()

    recipient_name = models.CharField(
        max_length=150,
    )

    phone_number = models.CharField(
        max_length=20,
    )

    province = models.CharField(
        max_length=100,
    )

    city = models.CharField(
        max_length=100,
    )

    postal_code = models.CharField(
        max_length=20,
    )

    address_line = models.TextField()

    building_number = models.CharField(
        max_length=30,
        blank=True,
    )

    unit_number = models.CharField(
        max_length=30,
        blank=True,
    )

    customer_note = models.TextField(
        blank=True,
    )

    reservation_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    inventory_released_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    expired_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-created_at",
        )

    def __str__(self) -> str:
        return (
            f"Order {self.public_id}"
        )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    product_name = models.CharField(
        max_length=180,
    )

    product_slug = models.SlugField(
        max_length=200,
    )

    sku = models.CharField(
        max_length=80,
    )

    material = models.CharField(
        max_length=10,
    )

    karat = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    purity = models.CharField(
        max_length=20,
        blank=True,
    )

    size = models.CharField(
        max_length=50,
        blank=True,
    )

    weight_grams = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
    )

    unit_price_rial = models.PositiveBigIntegerField()

    quantity = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "order",
                    "variant",
                ),
                name=(
                    "unique_variant_per_order"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    quantity__gte=1,
                ),
                name=(
                    "order_item_quantity_gte_1"
                ),
            ),
        ]

    @property
    def line_total_rial(self) -> int:
        return (
            self.unit_price_rial
            * self.quantity
        )

    def __str__(self) -> str:
        return (
            f"{self.sku} x "
            f"{self.quantity}"
        )