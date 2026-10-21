"""Audited, transactional shipment transitions for ELASI's single-parcel v1.

Payment verification is outside this module. In particular, there is no
administrative shortcut for turning a pending order into a paid order.
"""

from django.db import transaction
from django.utils import timezone

from .models import Order, Shipment
from .services import (
    OrderLifecycleError,
    _consume_inventory_for_locked_order,
)


def _shipment_text(value: str, *, label: str, max_length: int) -> str:
    normalized = str(value or "").strip()
    if (
        not normalized
        or len(normalized) > max_length
        or any(ord(char) < 32 or ord(char) == 127 for char in normalized)
    ):
        raise OrderLifecycleError(
            "invalid_shipment_field",
            f"{label} must be nonempty, contain no control characters, and "
            f"be at most {max_length} characters.",
        )
    return normalized


@transaction.atomic
def dispatch_order(*, order_id: int, carrier: str, tracking_code: str,
                   recorded_by=None, dispatched_at=None) -> Order:
    """Ship a verified paid order and consume reserved stock exactly once.

    Same tracking information on a shipped order is idempotent. A different
    tracking number requires an explicit, separately audited correction flow;
    silent overwrites of shipping history are intentionally prohibited.
    """
    carrier = _shipment_text(carrier, label="Carrier", max_length=80)
    tracking_code = _shipment_text(
        tracking_code, label="Tracking code", max_length=120,
    )
    now = dispatched_at or timezone.now()

    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise OrderLifecycleError("order_not_found", "Order was not found.") from exc

    if order.status == Order.Status.SHIPPED:
        try:
            existing = order.shipment
        except Shipment.DoesNotExist as exc:
            raise OrderLifecycleError(
                "shipment_missing", "Shipped order has no shipment record."
            ) from exc
        if existing.carrier == carrier and existing.tracking_code == tracking_code:
            return order
        raise OrderLifecycleError(
            "shipment_already_recorded", "Shipment details cannot be overwritten."
        )

    if order.status not in (Order.Status.PAID, Order.Status.PROCESSING):
        raise OrderLifecycleError(
            "invalid_order_state", "Only paid or processing orders can be dispatched."
        )
    if order.inventory_released_at is not None:
        raise OrderLifecycleError(
            "inventory_already_released", "Cannot dispatch an order whose stock was released."
        )
    if Shipment.objects.filter(order=order).exists():
        raise OrderLifecycleError(
            "shipment_already_recorded", "A shipment record already exists."
        )

    _consume_inventory_for_locked_order(order, consumed_at=now)

    Shipment.objects.create(
        order=order,
        carrier=carrier,
        tracking_code=tracking_code,
        shipped_at=now,
        recorded_by=recorded_by,
    )
    order.status = Order.Status.SHIPPED
    order.save(update_fields=("status", "updated_at"))
    return order


@transaction.atomic
def confirm_delivery(*, order_id: int, delivered_at=None) -> Order:
    """Confirm arrival; never touch stock or payment a second time."""
    now = delivered_at or timezone.now()
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise OrderLifecycleError("order_not_found", "Order was not found.") from exc

    if order.status == Order.Status.DELIVERED:
        return order
    if order.status != Order.Status.SHIPPED:
        raise OrderLifecycleError(
            "invalid_order_state", "Only shipped orders can be delivered."
        )
    if order.inventory_consumed_at is None:
        raise OrderLifecycleError(
            "inventory_not_consumed", "Shipment inventory has not been consumed."
        )
    try:
        shipment = order.shipment
    except Shipment.DoesNotExist as exc:
        raise OrderLifecycleError(
            "shipment_missing", "Shipment record is missing."
        ) from exc

    shipment.delivered_at = now
    shipment.save(update_fields=("delivered_at",))
    order.status = Order.Status.DELIVERED
    order.save(update_fields=("status", "updated_at"))
    return order
