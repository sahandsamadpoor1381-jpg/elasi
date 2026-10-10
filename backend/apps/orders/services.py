from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import InventoryBalance

from .models import Order, OrderItem


User = get_user_model()


class CheckoutError(Exception):
    def __init__(
        self,
        code: str,
        detail: str,
        *,
        available: int | None = None,
        sku: str | None = None,
    ):
        self.code = code
        self.detail = detail
        self.available = available
        self.sku = sku

        super().__init__(detail)


def validate_variant(
    variant: ProductVariant,
) -> None:
    if not variant.is_active:
        raise CheckoutError(
            "variant_inactive",
            "Product variant is not available.",
            sku=variant.sku,
        )

    if (
        variant.product.status
        != Product.Status.ACTIVE
    ):
        raise CheckoutError(
            "product_inactive",
            "Product is not available.",
            sku=variant.sku,
        )

    if not variant.product.category.is_active:
        raise CheckoutError(
            "category_inactive",
            "Product category is not available.",
            sku=variant.sku,
        )


@transaction.atomic
def checkout_cart(
    *,
    user: User,
    cart_token: UUID,
    recipient_name: str,
    phone_number: str,
    province: str,
    city: str,
    postal_code: str,
    address_line: str,
    building_number: str = "",
    unit_number: str = "",
    customer_note: str = "",
) -> Order:
    try:
        cart = (
            Cart.objects
            .select_for_update()
            .get(
                token=cart_token,
                status=Cart.Status.ACTIVE,
            )
        )
    except Cart.DoesNotExist as exc:
        raise CheckoutError(
            "cart_not_found",
            "Active cart was not found.",
        ) from exc

    if (
        cart.user_id is not None
        and cart.user_id != user.pk
    ):
        raise CheckoutError(
            "cart_owner_mismatch",
            "This cart belongs to another user.",
        )

    cart_items = list(
        CartItem.objects
        .select_related(
            "variant",
            "variant__product",
            "variant__product__category",
        )
        .filter(cart=cart)
        .order_by("variant_id")
    )

    if not cart_items:
        raise CheckoutError(
            "empty_cart",
            "Cart is empty.",
        )

    variant_ids = [
        item.variant_id
        for item in cart_items
    ]

    inventory_rows = list(
        InventoryBalance.objects
        .select_for_update()
        .filter(
            variant_id__in=variant_ids,
        )
        .order_by("variant_id")
    )

    inventory_by_variant = {
        inventory.variant_id: inventory
        for inventory in inventory_rows
    }

    subtotal_rial = 0

    for item in cart_items:
        variant = item.variant

        validate_variant(variant)

        inventory = inventory_by_variant.get(
            variant.pk,
        )

        available = (
            inventory.available
            if inventory is not None
            else 0
        )

        if item.quantity > available:
            raise CheckoutError(
                "stock_exceeded",
                (
                    "Requested quantity exceeds "
                    "available stock."
                ),
                available=available,
                sku=variant.sku,
            )

        subtotal_rial += (
            variant.price_rial
            * item.quantity
        )

    # V1:
    # هزینه ارسال پستی فعلاً صفر است.
    # بعداً از Shipping Service محاسبه می‌شود.
    shipping_fee_rial = 0

    total_rial = (
        subtotal_rial
        + shipping_fee_rial
    )

    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING_PAYMENT,
        shipping_method=(
            Order.ShippingMethod.POSTAL
        ),
        subtotal_rial=subtotal_rial,
        shipping_fee_rial=shipping_fee_rial,
        total_rial=total_rial,
        recipient_name=recipient_name,
        phone_number=phone_number,
        province=province,
        city=city,
        postal_code=postal_code,
        address_line=address_line,
        building_number=building_number,
        unit_number=unit_number,
        customer_note=customer_note,
    )

    order_items = []

    for item in cart_items:
        variant = item.variant

        order_items.append(
            OrderItem(
                order=order,
                variant=variant,
                product_name=(
                    variant.product.name
                ),
                product_slug=(
                    variant.product.slug
                ),
                sku=variant.sku,
                material=variant.material,
                karat=variant.karat,
                purity=variant.purity,
                size=variant.size,
                weight_grams=(
                    variant.weight_grams
                ),
                unit_price_rial=(
                    variant.price_rial
                ),
                quantity=item.quantity,
            )
        )

    OrderItem.objects.bulk_create(
        order_items,
    )

    for item in cart_items:
        inventory = (
            inventory_by_variant[
                item.variant_id
            ]
        )

        inventory.reserved += (
            item.quantity
        )

        inventory.save(
            update_fields=(
                "reserved",
                "updated_at",
            ),
        )

    if cart.user_id is None:
        cart.user = user

    cart.status = Cart.Status.CONVERTED

    cart.save(
        update_fields=(
            "user",
            "status",
            "updated_at",
        ),
    )

    return order