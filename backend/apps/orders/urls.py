from django.urls import path

from .views import (
    CheckoutAPIView,
    CustomerOrderListAPIView,
    CustomerOrderDetailAPIView,
)


app_name = "orders"


urlpatterns = [
    path("orders/", CustomerOrderListAPIView.as_view(), name="customer-order-list"),
    path("orders/<uuid:public_id>/", CustomerOrderDetailAPIView.as_view(), name="customer-order-detail"),
    path(
        "checkout/",
        CheckoutAPIView.as_view(),
        name="checkout",
    ),
]