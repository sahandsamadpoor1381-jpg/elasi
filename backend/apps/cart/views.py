from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
)
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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


def get_cart_token(
    request: Request,
) -> UUID:
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


def get_request_cart(
    request: Request,
) -> Cart:
    token = get_cart_token(
        request,
    )

    return get_object_or_404(
        get_cart_queryset(),
        token=token,
        status=Cart.Status.ACTIVE,
    )


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
        user = (
            request.user
            if request.user.is_authenticated
            else None
        )

        cart = Cart.objects.create(
            user=user,
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