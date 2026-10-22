from django.urls import path

from .views import (
    CheckoutAPIView,
    CheckoutShippingQuoteAPIView,
    CustomerOrderListAPIView,
    CustomerOrderDetailAPIView,
)


app_name = "orders"


urlpatterns = [
    path("orders/", CustomerOrderListAPIView.as_view(), name="customer-order-list"),
    path("orders/<uuid:public_id>/", CustomerOrderDetailAPIView.as_view(), name="customer-order-detail"),
    path(
        "checkout/shipping-quote/",
        CheckoutShippingQuoteAPIView.as_view(),
        name="shipping-quote",
    ),
    path(
        "checkout/",
        CheckoutAPIView.as_view(),
        name="checkout",
    ),
]