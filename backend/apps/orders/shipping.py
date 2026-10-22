"""ELASI v1 postal shipping policy.

No shipping fee is assumed: a merchant-approved flat rate must be explicitly
configured. A value of zero is allowed only when free shipping is approved.
Future province/weight based policies should replace this resolver without
changing the checkout's server-side pricing contract.
"""

from django.conf import settings


class ShippingFeeUnconfigured(Exception):
    """Checkout must fail closed until the merchant specifies shipping terms."""


def get_postal_shipping_fee_rial() -> int:
    fee = getattr(settings, "ELASI_POSTAL_SHIPPING_FEE_RIAL", -1)
    if (
        isinstance(fee, bool)
        or not isinstance(fee, int)
        or fee < 0
        or fee > 2**63 - 1
        or fee % 10 != 0  # Storefront displays whole Toman.
    ):
        raise ShippingFeeUnconfigured(
            "Postal shipping fee is not configured for checkout."
        )
    return fee
