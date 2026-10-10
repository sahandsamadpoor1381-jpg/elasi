from django.urls import path

from .views import CheckoutAPIView


app_name = "orders"


urlpatterns = [
    path(
        "checkout/",
        CheckoutAPIView.as_view(),
        name="checkout",
    ),
]