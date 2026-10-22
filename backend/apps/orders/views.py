from rest_framework import status, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api import get_cart_token

from .shipping import ShippingFeeUnconfigured, get_postal_shipping_fee_rial
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

    response_status = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if error.code == "shipping_fee_unconfigured"
        else status.HTTP_400_BAD_REQUEST
    )
    return Response(payload, status=response_status)


class CheckoutShippingQuoteAPIView(APIView):
    """Public to logged-in customers; shipping amount is always server-owned."""
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        try:
            fee = get_postal_shipping_fee_rial()
        except ShippingFeeUnconfigured:
            return Response(
                {
                    "code": "shipping_fee_unconfigured",
                    "detail": "Shipping terms are not configured.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                headers={"Cache-Control": "no-store"},
            )

        return Response({
            "shipping_method": Order.ShippingMethod.POSTAL,
            "shipping_fee_rial": fee,
        }, headers={"Cache-Control": "no-store"})


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

class CustomerOrderPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 20


class CustomerOrderListAPIView(generics.ListAPIView):
    """Return only the authenticated customer's orders."""
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    pagination_class = CustomerOrderPagination

    def get_queryset(self):
        return (Order.objects.filter(user=self.request.user)
                .prefetch_related("items", "shipment"))


class CustomerOrderDetailAPIView(generics.RetrieveAPIView):
    """A UUID is not authorization; always filter by owner."""
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return (Order.objects.filter(user=self.request.user)
                .prefetch_related("items", "shipment"))
