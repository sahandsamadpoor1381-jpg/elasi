from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from apps.catalog.models import Product, ProductVariant

from .models import Cart, CartItem


class CartServiceError(Exception):
    def __init__(
        self,
        code: str,
        detail: str,
        *,
        available: int | None = None,
    ):
        self.code = code
        self.detail = detail
        self.available = available

        super().__init__(detail)


def get_variant_available(
    variant: ProductVariant,
) -> int:
    try:
        return variant.inventory.available
    except ObjectDoesNotExist:
        return 0


def validate_variant_for_cart(
    variant: ProductVariant,
) -> None:
    if not variant.is_active:
        raise CartServiceError(
            "variant_inactive",
            "This product variant is not available.",
        )

    if (
        variant.product.status
        != Product.Status.ACTIVE
    ):
        raise CartServiceError(
            "product_inactive",
            "This product is not available.",
        )

    if not variant.product.category.is_active:
        raise CartServiceError(
            "category_inactive",
            "This product is not available.",
        )


@transaction.atomic
def add_item_to_cart(
    *,
    cart: Cart,
    variant_sku: str,
    quantity: int,
) -> tuple[CartItem, bool]:
    if quantity < 1:
        raise CartServiceError(
            "invalid_quantity",
            "Quantity must be at least 1.",
        )

    locked_cart = (
        Cart.objects.select_for_update()
        .get(
            pk=cart.pk,
            status=Cart.Status.ACTIVE,
        )
    )

    try:
        variant = (
            ProductVariant.objects
            .select_related(
                "product",
                "product__category",
                "inventory",
            )
            .get(
                sku=variant_sku,
            )
        )
    except ProductVariant.DoesNotExist as exc:
        raise CartServiceError(
            "variant_not_found",
            "Product variant was not found.",
        ) from exc

    validate_variant_for_cart(
        variant,
    )

    available = get_variant_available(
        variant,
    )

    try:
        item = (
            CartItem.objects
            .select_for_update()
            .get(
                cart=locked_cart,
                variant=variant,
            )
        )

        desired_quantity = (
            item.quantity + quantity
        )

        created = False

    except CartItem.DoesNotExist:
        item = CartItem(
            cart=locked_cart,
            variant=variant,
        )

        desired_quantity = quantity
        created = True

    if desired_quantity > available:
        raise CartServiceError(
            "stock_exceeded",
            "Requested quantity exceeds available stock.",
            available=available,
        )

    item.quantity = desired_quantity
    item.save()

    return item, created


@transaction.atomic
def set_cart_item_quantity(
    *,
    cart: Cart,
    item_id: int,
    quantity: int,
) -> CartItem:
    if quantity < 1:
        raise CartServiceError(
            "invalid_quantity",
            "Quantity must be at least 1.",
        )

    locked_cart = (
        Cart.objects.select_for_update()
        .get(
            pk=cart.pk,
            status=Cart.Status.ACTIVE,
        )
    )

    try:
        item = (
            CartItem.objects
            .select_for_update()
            .select_related(
                "variant",
                "variant__product",
                "variant__product__category",
            )
            .get(
                pk=item_id,
                cart=locked_cart,
            )
        )
    except CartItem.DoesNotExist as exc:
        raise CartServiceError(
            "item_not_found",
            "Cart item was not found.",
        ) from exc

    validate_variant_for_cart(
        item.variant,
    )

    available = get_variant_available(
        item.variant,
    )

    if quantity > available:
        raise CartServiceError(
            "stock_exceeded",
            "Requested quantity exceeds available stock.",
            available=available,
        )

    item.quantity = quantity

    item.save(
        update_fields=(
            "quantity",
            "updated_at",
        ),
    )

    return item


@transaction.atomic
def remove_cart_item(
    *,
    cart: Cart,
    item_id: int,
) -> None:
    locked_cart = (
        Cart.objects.select_for_update()
        .get(
            pk=cart.pk,
            status=Cart.Status.ACTIVE,
        )
    )

    deleted_count, _ = (
        CartItem.objects
        .filter(
            pk=item_id,
            cart=locked_cart,
        )
        .delete()
    )

    if deleted_count == 0:
        raise CartServiceError(
            "item_not_found",
            "Cart item was not found.",
        )