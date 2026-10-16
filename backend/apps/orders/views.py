from rest_framework import status
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api import get_cart_token

from .models import Order
from .serializers import (
    CheckoutSerializer,
    OrderSerializer,
)
from .services import (
    CheckoutError,
    checkout_cart,
)


def checkout_error_response(
    error: CheckoutError,
) -> Response:
    payload = {
        "code": error.code,
        "detail": error.detail,
    }

    if error.available is not None:
        payload["available"] = (
            error.available
        )

    if error.sku is not None:
        payload["sku"] = error.sku

    return Response(
        payload,
        status=status.HTTP_400_BAD_REQUEST,
    )


class CheckoutAPIView(APIView):
    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        serializer = CheckoutSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        cart_token = get_cart_token(
            request,
        )

        try:
            order = checkout_cart(
                user=request.user,
                cart_token=cart_token,
                **serializer.validated_data,
            )
        except CheckoutError as error:
            return checkout_error_response(
                error,
            )

        order = (
            Order.objects
            .prefetch_related("items")
            .get(pk=order.pk)
        )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )