from django.urls import path

from .views import (
    CartAPIView,
    CartItemCollectionAPIView,
    CartItemDetailAPIView,
)


app_name = "cart"


urlpatterns = [
    path(
        "cart/",
        CartAPIView.as_view(),
        name="cart",
    ),
    path(
        "cart/items/",
        CartItemCollectionAPIView.as_view(),
        name="cart-item-collection",
    ),
    path(
        "cart/items/<int:item_id>/",
        CartItemDetailAPIView.as_view(),
        name="cart-item-detail",
    ),
]