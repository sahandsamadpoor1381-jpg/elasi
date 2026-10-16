from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api import get_cart_token

from .models import Cart
from .serializers import (
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
)
from .services import (
    CartServiceError,
    add_item_to_cart,
    remove_cart_item,
    set_cart_item_quantity,
)


def get_cart_queryset():
    return (
        Cart.objects
        .select_related("user")
        .prefetch_related(
            "items__variant__product__images",
            "items__variant__inventory",
        )
    )


def get_request_cart(
    request: Request,
) -> Cart:
    """
    Resolve the cart addressed by ``X-Cart-Token`` with a strict
    ownership policy:

    - A cart bound to a user is visible and modifiable only by
      that user (never by anonymous requests or other users —
      even when the token is known). Foreign carts raise 404 so
      token leaks reveal nothing.
    - An unbound guest cart is claimed by the first authenticated
      user that touches it. This preserves guest carts across the
      OTP login flow (the token lives in browser storage and the
      cart becomes the user's cart on the next request). The claim
      runs inside a transaction under a row lock and re-checks the
      ownership state, so two users racing for the same token can
      never both claim it or overwrite each other's ownership.
    - Anonymous requests against unbound carts keep the original
      capability-token behavior with no regression.
    """

    token = get_cart_token(
        request,
    )

    cart = get_object_or_404(
        get_cart_queryset(),
        token=token,
        status=Cart.Status.ACTIVE,
    )

    if cart.user_id is not None:
        if (
            not request.user.is_authenticated
            or cart.user_id != request.user.pk
        ):
            raise NotFound(
                "Cart was not found.",
            )

        return cart

    if request.user.is_authenticated:
        with transaction.atomic():
            locked_cart = (
                Cart.objects
                .select_for_update()
                .get(
                    pk=cart.pk,
                )
            )

            if (
                locked_cart.status
                != Cart.Status.ACTIVE
            ) or (
                locked_cart.user_id is not None
                and locked_cart.user_id != request.user.pk
            ):
                # A concurrent request claimed or converted the
                # cart between our read and the lock. Ownership
                # already belongs to someone else (or the cart is
                # gone) — never overwrite it.
                raise NotFound(
                    "Cart was not found.",
                )

            if locked_cart.user_id is None:
                locked_cart.user = request.user

                locked_cart.save(
                    update_fields=(
                        "user",
                        "updated_at",
                    ),
                )

            return locked_cart

    return cart


def cart_service_error_response(
    error: CartServiceError,
) -> Response:
    payload = {
        "code": error.code,
        "detail": error.detail,
    }

    if error.available is not None:
        payload["available"] = (
            error.available
        )

    return Response(
        payload,
        status=status.HTTP_400_BAD_REQUEST,
    )


class CartAPIView(APIView):
    permission_classes = (
        AllowAny,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        """
        Create (or return) the requester's active cart.

        - Authenticated users get-or-create a single active cart
          bound to their account, so a login on a new device
          recovers the same cart.
        - Anonymous requests create a fresh guest cart, exactly
          as before.
        """

        if request.user.is_authenticated:
            existing = (
                Cart.objects
                .filter(
                    user=request.user,
                    status=Cart.Status.ACTIVE,
                )
                .order_by("-updated_at")
                .first()
            )

            if existing is not None:
                cart = get_cart_queryset().get(
                    pk=existing.pk,
                )

                return Response(
                    CartSerializer(
                        cart,
                        context={
                            "request": request,
                        },
                    ).data,
                    status=status.HTTP_200_OK,
                )

            cart = Cart.objects.create(
                user=request.user,
            )

        else:
            cart = Cart.objects.create(
                user=None,
            )

        cart = get_cart_queryset().get(
            pk=cart.pk,
        )

        return Response(
            CartSerializer(
                cart,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def get(
        self,
        request: Request,
    ) -> Response:
        cart = get_request_cart(
            request,
        )

        return Response(
            CartSerializer(
                cart,
                context={
                    "request": request,
                },
            ).data,
        )


class CartItemCollectionAPIView(
    APIView,
):
    permission_classes = (
        AllowAny,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        cart = get_request_cart(
            request,
        )

        serializer = (
            CartItemCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            _, created = (
                add_item_to_cart(
                    cart=cart,
                    variant_sku=(
                        serializer
                        .validated_data[
                            "variant_sku"
                        ]
                    ),
                    quantity=(
                        serializer
                        .validated_data[
                            "quantity"
                        ]
                    ),
                )
            )
        except CartServiceError as error:
            return (
                cart_service_error_response(
                    error,
                )
            )

        refreshed_cart = (
            get_cart_queryset().get(
                pk=cart.pk,
            )
        )

        return Response(
            CartSerializer(
                refreshed_cart,
                context={
                    "request": request,
                },
            ).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class CartItemDetailAPIView(
    APIView,
):
    permission_classes = (
        AllowAny,
    )

    def patch(
        self,
        request: Request,
        item_id: int,
    ) -> Response:
        cart = get_request_cart(
            request,
        )

        serializer = (
            CartItemUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            set_cart_item_quantity(
                cart=cart,
                item_id=item_id,
                quantity=(
                    serializer
                    .validated_data[
                        "quantity"
                    ]
                ),
            )
        except CartServiceError as error:
            return (
                cart_service_error_response(
                    error,
                )
            )

        refreshed_cart = (
            get_cart_queryset().get(
                pk=cart.pk,
            )
        )

        return Response(
            CartSerializer(
                refreshed_cart,
                context={
                    "request": request,
                },
            ).data,
        )

    def delete(
        self,
        request: Request,
        item_id: int,
    ) -> Response:
        cart = get_request_cart(
            request,
        )

        try:
            remove_cart_item(
                cart=cart,
                item_id=item_id,
            )
        except CartServiceError as error:
            return (
                cart_service_error_response(
                    error,
                )
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
