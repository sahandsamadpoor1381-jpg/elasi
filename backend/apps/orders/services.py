from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import InventoryBalance

from .models import Order, OrderItem


User = get_user_model()


DEFAULT_PAYMENT_RESERVATION_MINUTES = 15


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


class OrderLifecycleError(Exception):
    def __init__(
        self,
        code: str,
        detail: str,
    ):
        self.code = code
        self.detail = detail

        super().__init__(detail)


def get_payment_reservation_duration() -> timedelta:
    raw_minutes = getattr(
        settings,
        "ORDER_PAYMENT_RESERVATION_MINUTES",
        DEFAULT_PAYMENT_RESERVATION_MINUTES,
    )

    try:
        minutes = int(
            raw_minutes,
        )
    except (
        TypeError,
        ValueError,
    ):
        minutes = (
            DEFAULT_PAYMENT_RESERVATION_MINUTES
        )

    if minutes <= 0:
        minutes = (
            DEFAULT_PAYMENT_RESERVATION_MINUTES
        )

    return timedelta(
        minutes=minutes,
    )


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


def _release_inventory_for_locked_order(
    order: Order,
    *,
    released_at,
) -> bool:
    """
    Release an order's inventory reservation exactly once.

    The caller must already hold a SELECT FOR UPDATE lock
    on the Order row and run inside transaction.atomic().
    """

    if (
        order.inventory_released_at
        is not None
    ):
        return False

    order_items = list(
        OrderItem.objects
        .filter(
            order=order,
        )
        .order_by(
            "variant_id",
        )
    )

    if not order_items:
        raise OrderLifecycleError(
            "order_has_no_items",
            "Order has no items.",
        )

    variant_ids = [
        item.variant_id
        for item in order_items
    ]

    inventory_rows = list(
        InventoryBalance.objects
        .select_for_update()
        .filter(
            variant_id__in=variant_ids,
        )
        .order_by(
            "variant_id",
        )
    )

    inventory_by_variant = {
        inventory.variant_id:
            inventory
        for inventory in inventory_rows
    }

    for item in order_items:
        inventory = (
            inventory_by_variant.get(
                item.variant_id,
            )
        )

        if inventory is None:
            raise OrderLifecycleError(
                "inventory_missing",
                (
                    "Inventory balance is missing "
                    f"for SKU {item.sku}."
                ),
            )

        if (
            inventory.reserved
            < item.quantity
        ):
            raise OrderLifecycleError(
                "inventory_reservation_inconsistent",
                (
                    "Reserved inventory is lower "
                    "than the order reservation "
                    f"for SKU {item.sku}."
                ),
            )

    for item in order_items:
        inventory = (
            inventory_by_variant[
                item.variant_id
            ]
        )

        inventory.reserved -= (
            item.quantity
        )

        inventory.save(
            update_fields=(
                "reserved",
                "updated_at",
            ),
        )

    order.inventory_released_at = (
        released_at
    )

    order.save(
        update_fields=(
            "inventory_released_at",
            "updated_at",
        ),
    )

    return True


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
        .filter(
            cart=cart,
        )
        .order_by(
            "variant_id",
        )
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
        .order_by(
            "variant_id",
        )
    )

    inventory_by_variant = {
        inventory.variant_id:
            inventory
        for inventory in inventory_rows
    }

    subtotal_rial = 0

    for item in cart_items:
        variant = item.variant

        validate_variant(
            variant,
        )

        inventory = (
            inventory_by_variant.get(
                variant.pk,
            )
        )

        available = (
            inventory.available
            if inventory is not None
            else 0
        )

        if (
            item.quantity >
            available
        ):
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

    shipping_fee_rial = 0

    total_rial = (
        subtotal_rial
        + shipping_fee_rial
    )

    reservation_expires_at = (
        timezone.now()
        + get_payment_reservation_duration()
    )

    order = Order.objects.create(
        user=user,
        status=(
            Order.Status.PENDING_PAYMENT
        ),
        shipping_method=(
            Order.ShippingMethod.POSTAL
        ),
        subtotal_rial=subtotal_rial,
        shipping_fee_rial=(
            shipping_fee_rial
        ),
        total_rial=total_rial,
        recipient_name=recipient_name,
        phone_number=phone_number,
        province=province,
        city=city,
        postal_code=postal_code,
        address_line=address_line,
        building_number=(
            building_number
        ),
        unit_number=(
            unit_number
        ),
        customer_note=(
            customer_note
        ),
        reservation_expires_at=(
            reservation_expires_at
        ),
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
                material=(
                    variant.material
                ),
                karat=(
                    variant.karat
                ),
                purity=(
                    variant.purity
                ),
                size=(
                    variant.size
                ),
                weight_grams=(
                    variant.weight_grams
                ),
                unit_price_rial=(
                    variant.price_rial
                ),
                quantity=(
                    item.quantity
                ),
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

    if (
        cart.user_id
        is None
    ):
        cart.user = user

    cart.status = (
        Cart.Status.CONVERTED
    )

    cart.save(
        update_fields=(
            "user",
            "status",
            "updated_at",
        ),
    )

    return order


def cancel_pending_order(
    *,
    order_id: int,
) -> Order:
    now = timezone.now()

    with transaction.atomic():
        try:
            order = (
                Order.objects
                .select_for_update()
                .get(
                    pk=order_id,
                )
            )
        except Order.DoesNotExist as exc:
            raise OrderLifecycleError(
                "order_not_found",
                "Order was not found.",
            ) from exc

        if (
            order.status
            == Order.Status.CANCELLED
        ):
            return order

        if (
            order.status
            != Order.Status.PENDING_PAYMENT
        ):
            raise OrderLifecycleError(
                "invalid_order_state",
                (
                    "Only a pending-payment order "
                    "can be cancelled by this service."
                ),
            )

        _release_inventory_for_locked_order(
            order,
            released_at=now,
        )

        order.status = (
            Order.Status.CANCELLED
        )

        order.cancelled_at = (
            now
        )

        order.save(
            update_fields=(
                "status",
                "cancelled_at",
                "updated_at",
            ),
        )

        return order


def expire_pending_order(
    *,
    order_id: int,
    now=None,
) -> Order:
    effective_now = (
        now
        or timezone.now()
    )

    with transaction.atomic():
        try:
            order = (
                Order.objects
                .select_for_update()
                .get(
                    pk=order_id,
                )
            )
        except Order.DoesNotExist as exc:
            raise OrderLifecycleError(
                "order_not_found",
                "Order was not found.",
            ) from exc

        if (
            order.status
            == Order.Status.EXPIRED
        ):
            return order

        if (
            order.status
            != Order.Status.PENDING_PAYMENT
        ):
            raise OrderLifecycleError(
                "invalid_order_state",
                (
                    "Only a pending-payment order "
                    "can expire."
                ),
            )

        if (
            order.reservation_expires_at
            is None
        ):
            raise OrderLifecycleError(
                "reservation_deadline_missing",
                (
                    "Order reservation expiration "
                    "time is missing."
                ),
            )

        if (
            order.reservation_expires_at
            > effective_now
        ):
            raise OrderLifecycleError(
                "reservation_not_expired",
                (
                    "Order reservation has not "
                    "expired yet."
                ),
            )

        _release_inventory_for_locked_order(
            order,
            released_at=(
                effective_now
            ),
        )

        order.status = (
            Order.Status.EXPIRED
        )

        order.expired_at = (
            effective_now
        )

        order.save(
            update_fields=(
                "status",
                "expired_at",
                "updated_at",
            ),
        )

        return order


def mark_order_paid(
    *,
    order_id: int,
    paid_at=None,
) -> Order:
    effective_paid_at = (
        paid_at
        or timezone.now()
    )

    lifecycle_error = None
    result_order = None

    with transaction.atomic():
        try:
            order = (
                Order.objects
                .select_for_update()
                .get(
                    pk=order_id,
                )
            )
        except Order.DoesNotExist as exc:
            raise OrderLifecycleError(
                "order_not_found",
                "Order was not found.",
            ) from exc

        if (
            order.status
            == Order.Status.PAID
        ):
            return order

        if (
            order.status
            != Order.Status.PENDING_PAYMENT
        ):
            raise OrderLifecycleError(
                "invalid_order_state",
                (
                    "Only a pending-payment order "
                    "can be marked as paid."
                ),
            )

        if (
            order.reservation_expires_at
            is not None
            and
            order.reservation_expires_at
            <= effective_paid_at
        ):
            _release_inventory_for_locked_order(
                order,
                released_at=(
                    effective_paid_at
                ),
            )

            order.status = (
                Order.Status.EXPIRED
            )

            order.expired_at = (
                effective_paid_at
            )

            order.save(
                update_fields=(
                    "status",
                    "expired_at",
                    "updated_at",
                ),
            )

            result_order = order

            lifecycle_error = (
                OrderLifecycleError(
                    "reservation_expired",
                    (
                        "Order reservation expired "
                        "before payment confirmation."
                    ),
                )
            )
        else:
            order.status = (
                Order.Status.PAID
            )

            order.paid_at = (
                effective_paid_at
            )

            order.save(
                update_fields=(
                    "status",
                    "paid_at",
                    "updated_at",
                ),
            )

            result_order = order

    if (
        lifecycle_error
        is not None
    ):
        raise lifecycle_error

    if (
        result_order
        is None
    ):
        raise OrderLifecycleError(
            "payment_transition_failed",
            (
                "Order payment transition "
                "did not complete."
            ),
        )

    return result_order


def expire_stale_pending_orders(
    *,
    now=None,
    limit: int = 100,
) -> int:
    effective_now = (
        now
        or timezone.now()
    )

    if limit <= 0:
        return 0

    order_ids = list(
        Order.objects
        .filter(
            status=(
                Order.Status.PENDING_PAYMENT
            ),
            reservation_expires_at__isnull=False,
            reservation_expires_at__lte=(
                effective_now
            ),
        )
        .order_by(
            "reservation_expires_at",
            "pk",
        )
        .values_list(
            "pk",
            flat=True,
        )[:limit]
    )

    expired_count = 0

    for order_id in order_ids:
        try:
            expire_pending_order(
                order_id=order_id,
                now=effective_now,
            )
        except OrderLifecycleError as error:
            if (
                error.code
                == "invalid_order_state"
            ):
                continue

            raise

        expired_count += 1

    return expired_count