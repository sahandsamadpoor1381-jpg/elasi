"""
Shared API-layer helpers used by more than one app.
"""

from uuid import UUID

from rest_framework.exceptions import ValidationError
from rest_framework.request import Request


def get_cart_token(
    request: Request,
) -> UUID:
    """
    Extract and validate the ``X-Cart-Token`` header.

    Single implementation shared by the cart and checkout APIs so
    the two endpoints cannot drift apart.
    """

    raw_token = request.headers.get(
        "X-Cart-Token",
    )

    if not raw_token:
        raise ValidationError(
            {
                "cart_token": (
                    "X-Cart-Token header "
                    "is required."
                ),
            },
        )

    try:
        return UUID(raw_token)
    except ValueError as exc:
        raise ValidationError(
            {
                "cart_token": (
                    "Invalid cart token."
                ),
            },
        ) from exc
