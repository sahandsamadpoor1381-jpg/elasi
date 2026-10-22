from django.contrib.auth import get_user_model
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
    return variant.get_available()


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

@transaction.atomic
def claim_guest_cart_for_user(*, cart_id: int, user) -> Cart:
    """Claim a guest cart, merging it into an existing active account cart.

    Cart locks protect item writes; the user-row lock serializes account cart
    creation and multiple guest claims for the same user on PostgreSQL.
    The existing account cart remains canonical so another device keeps its
    token. We keep *all* requested quantities, even if stock has since fallen:
    the cart does not reserve inventory and checkout revalidates atomically.
    """
    from rest_framework.exceptions import NotFound

    guest = Cart.objects.select_for_update().get(pk=cart_id)
    if guest.status != Cart.Status.ACTIVE or (
        guest.user_id is not None and guest.user_id != user.pk
    ):
        raise NotFound("Cart was not found.")

    if guest.user_id == user.pk:
        return guest

    # Acquired after the guest lock. All authenticated cart creation uses
    # the same user-row lock to prevent two active carts being created.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    account_cart = (
        Cart.objects.select_for_update()
        .filter(user_id=user.pk, status=Cart.Status.ACTIVE)
        .exclude(pk=guest.pk)
        .order_by("-updated_at", "-pk")
        .first()
    )
    if account_cart is None:
        guest.user = user
        guest.save(update_fields=("user", "updated_at"))
        return guest

    account_items = {
        item.variant_id: item
        for item in CartItem.objects.select_for_update().filter(cart=account_cart)
    }
    guest_items = list(
        CartItem.objects.select_for_update()
        .filter(cart=guest)
        .order_by("variant_id")
    )
    for guest_item in guest_items:
        account_item = account_items.get(guest_item.variant_id)
        if account_item is None:
            guest_item.cart = account_cart
            guest_item.save(update_fields=("cart", "updated_at"))
        else:
            account_item.quantity += guest_item.quantity
            account_item.save(update_fields=("quantity", "updated_at"))
            guest_item.delete()

    guest.user = user
    guest.status = Cart.Status.ABANDONED
    guest.save(update_fields=("user", "status", "updated_at"))
    account_cart.save(update_fields=("updated_at",))
    return account_cart
